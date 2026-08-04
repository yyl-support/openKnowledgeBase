from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Dict, List

from .ports import GitSourceRepository, MetadataRepository, ModelRegistry, WikiRepository
from .wiki_validation import validate_wiki_contract


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "-", value).strip("-")
    return slug or "wiki"


class KnowledgeApplication:
    def __init__(
        self,
        workspace: Path,
        store: MetadataRepository,
        models: ModelRegistry,
        git_sources: GitSourceRepository,
        wiki: WikiRepository,
    ):
        self.workspace = workspace
        self.store = store
        self.models = models
        self.git_sources = git_sources
        self.wiki = wiki

    def initialize(self) -> Dict[str, str]:
        self.store.initialize()
        for directory in (
            "sources",
            "normalized",
            "claims",
            "candidates",
            "wiki",
        ):
            (self.workspace / directory).mkdir(exist_ok=True)
        self.wiki.initialize()
        return {"workspace": str(self.workspace), "status": "initialized"}

    def add_git_source(
        self,
        repository: Path,
        reference: str,
        title: str,
        includes: List[str],
        canonical_url: str = None,
    ) -> Dict[str, Any]:
        revision = self.git_sources.resolve(repository, reference)
        canonical_repository = str(repository.resolve())
        canonical_identity = (canonical_url or canonical_repository).rstrip("/")
        normalized_includes = self._normalize_includes(includes)
        scope_identity = ",".join(normalized_includes) or "*"
        identity = f"{canonical_identity}@{revision}#{scope_identity}"
        existing = self.store.find_one("source", "identity", identity)
        if existing:
            self.verify_source_integrity(existing["id"])
            return existing

        source_id = stable_id("source-git", identity)
        destination = self.workspace / "sources" / source_id
        if destination.exists():
            return self._recover_source_record(destination, identity)

        temporary = Path(
            tempfile.mkdtemp(prefix=f".{source_id}-", dir=str(destination.parent))
        )
        snapshot = temporary / "snapshot"
        snapshot.mkdir()
        self.git_sources.snapshot(
            repository, revision, snapshot, normalized_includes
        )
        if not any(snapshot.rglob("*")):
            raise ValueError("Git Source scope matched no tracked files")

        record = {
            "id": source_id,
            "identity": identity,
            "title": title,
            "source_type": "git",
            "canonical_url": canonical_url,
            "visibility": "public",
            "status": "active",
            "revision": revision,
            "content_hash": self._directory_hash(snapshot),
            "scope": {"includes": normalized_includes},
            "human_location": (
                f"Git repository {canonical_identity} at {revision[:12]}"
                + (f", scope {', '.join(normalized_includes)}" if normalized_includes else "")
            ),
            "machine_locator": {
                "repository": canonical_repository,
                "canonical_url": canonical_url,
                "revision": revision,
                "includes": normalized_includes,
            },
            "created_at": now(),
        }
        (temporary / "manifest.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        temporary.replace(destination)
        self.store.put("source", record)
        return record

    def _normalize_includes(self, includes: List[str]) -> List[str]:
        normalized = []
        for include in includes:
            value = include.strip().lstrip("./").rstrip("/")
            if not value or value == ".":
                continue
            path = Path(value)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"Invalid Git Source include path: {include}")
            normalized.append(f"{value}/")
        return sorted(set(normalized))

    def _split_blocks(self, content: str) -> List[Dict[str, Any]]:
        lines = content.splitlines()
        blocks = []
        block_number = 0
        current_start = None
        current_lines = []
        for index, line in enumerate(lines, start=1):
            if line.startswith("#") and current_lines:
                blocks.append(
                    self._make_block(block_number, current_start, current_lines)
                )
                block_number += 1
                current_lines = []
                current_start = None
            if current_start is None and line.strip():
                current_start = index
            if current_start is not None:
                current_lines.append(line)
        if current_lines:
            blocks.append(
                self._make_block(block_number, current_start, current_lines)
            )
        if not blocks:
            raise ValueError("Source text produced no semantic blocks")
        return blocks

    def _make_block(
        self, number: int, start: int, lines: List[str]
    ) -> Dict[str, Any]:
        trimmed = list(lines)
        while trimmed and not trimmed[0].strip():
            trimmed.pop(0)
            start += 1
        while trimmed and not trimmed[-1].strip():
            trimmed.pop()
        text = "\n".join(trimmed)
        return {
            "id": f"b{number + 1}",
            "line_start": start,
            "line_end": start + len(trimmed) - 1,
            "content": text,
        }

    def normalize(self, source_id: str) -> Dict[str, Any]:
        source = self.store.get("source", source_id)
        self.verify_source_integrity(source_id)
        normalized_id = stable_id("normalized", f"{source_id}@{source['revision']}")
        existing = self.store.find_one("normalized", "id", normalized_id)
        if existing:
            return existing

        snapshot = self.workspace / "sources" / source_id / "snapshot"
        files = self._read_text_files(snapshot)
        sections = []
        for path, content in files:
            blocks = self._split_blocks(content)
            sections.append(
                {
                    "path": path,
                    "content": content,
                    "blocks": blocks,
                    "human_location": f"{source['title']} / {path}",
                    "machine_locator": {
                        "source_id": source_id,
                        "source_revision": source["revision"],
                        "path": path,
                    },
                }
            )
        combined = "\n\n".join(
            f"# File: {section['path']}\n\n{section['content']}"
            for section in sections
        )
        record = {
            "id": normalized_id,
            "source_id": source_id,
            "source_revision": source["revision"],
            "status": "generated",
            "content": combined,
            "sections": sections,
            "warnings": [],
            "created_at": now(),
        }
        self.store.put("normalized", record)
        path = self.workspace / "normalized" / f"{normalized_id}.json"
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        return record

    def verify_source_integrity(self, source_id: str) -> Dict[str, Any]:
        source = self.store.get("source", source_id)
        snapshot = self.workspace / "sources" / source_id / "snapshot"
        actual_hash = self._directory_hash(snapshot)
        if actual_hash != source["content_hash"]:
            raise ValueError(f"Source integrity check failed: {source_id}")
        return {"source_id": source_id, "status": "verified"}

    def extract_claims(
        self, normalized_id: str, model_name: str, instruction_file: Path = None
    ) -> List[Dict[str, Any]]:
        normalized = self.store.get("normalized", normalized_id)
        source = self.store.get("source", normalized["source_id"])
        self.verify_source_integrity(source["id"])
        if normalized["source_revision"] != source["revision"]:
            raise ValueError("Normalized document does not match current Source revision")
        instructions, instruction_hash = self._load_instructions(instruction_file)
        model = self.models.get(model_name)
        extracted = model.extract_claims(normalized, instructions)
        records = []
        for item in extracted:
            identity = f"{normalized_id}:{item['statement']}"
            claim_id = stable_id("claim", identity)
            existing = self.store.find_one("claim", "id", claim_id)
            if existing:
                records.append(existing)
                continue
            record = {
                "id": claim_id,
                "statement": item["statement"],
                "claim_type": item["claim_type"],
                "authors": [model.name],
                "review_status": "pending-review",
                "evidence_status": "unverified",
                "generation_instruction_hash": instruction_hash,
                "source_refs": [
                    {
                        "source_id": source["id"],
                        "source_revision": source["revision"],
                        "relation": "supports",
                        "evidence_quote": item["evidence_quote"],
                        "human_location": item["human_location"],
                        "machine_locator": item["machine_locator"],
                    }
                ],
                "normalized_document_id": normalized_id,
                "created_at": now(),
            }
            self.store.put("claim", record)
            records.append(record)
        path = self.workspace / "claims" / f"{normalized_id}.json"
        path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        return records

    def build_wiki_candidate(
        self, source_id: str, model_name: str, instruction_file: Path = None
    ) -> Dict[str, Any]:
        source = self.store.get("source", source_id)
        self.verify_source_integrity(source_id)
        claims = [
            claim
            for claim in self.store.list("claim")
            if any(ref["source_id"] == source_id for ref in claim["source_refs"])
        ]
        if not claims:
            raise ValueError("No claims exist for this source; run claims extract first")
        instructions, instruction_hash = self._load_instructions(instruction_file)
        model = self.models.get(model_name)
        content = model.build_wiki(source, claims, instructions)
        validate_wiki_contract(content)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        candidate_id = stable_id(
            "wiki-candidate",
            f"{source_id}:{source['revision']}:{instruction_hash}:{content_hash}",
        )
        existing = self.store.find_one("candidate", "id", candidate_id)
        if existing:
            return existing
        record = {
            "id": candidate_id,
            "title": source["title"],
            "slug": f"{slugify(source['title'])}--{source_id.removeprefix('source-git-')}",
            "source_id": source_id,
            "source_revision": source["revision"],
            "claim_ids": [claim["id"] for claim in claims],
            "authors": [model.name],
            "status": "pending-review",
            "authority": "informative",
            "visibility": source["visibility"],
            "generation_instruction_hash": instruction_hash,
            "content": content,
            "created_at": now(),
        }
        self.store.put("candidate", record)
        path = self.workspace / "candidates" / f"{candidate_id}.json"
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        return record

    def validate_wiki_file(self, path: Path) -> Dict[str, Any]:
        content = path.read_text(encoding="utf-8")
        validate_wiki_contract(content)
        return {"path": str(path), "status": "valid"}

    def _load_instructions(self, instruction_file: Path):
        if instruction_file is None:
            return "", "none"
        content = instruction_file.read_text(encoding="utf-8")
        instruction_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return content.strip(), instruction_hash

    def list_claims(self, source_id: str) -> List[Dict[str, Any]]:
        self.verify_source_integrity(source_id)
        return [
            claim
            for claim in self.store.list("claim")
            if any(ref["source_id"] == source_id for ref in claim["source_refs"])
        ]

    def approve_candidate(
        self, candidate_id: str, reviewer: str
    ) -> Dict[str, Any]:
        candidate = self.store.get("candidate", candidate_id)
        source = self.store.get("source", candidate["source_id"])
        self.verify_source_integrity(source["id"])
        if source["status"] != "active":
            raise ValueError("Candidate source is not active")
        if candidate["status"] == "approved":
            return candidate
        approved = dict(candidate)
        approved.update(
            {
                "status": "approved",
                "reviewers": [reviewer],
                "approved_at": now(),
            }
        )
        wiki_path = f"{candidate['slug']}.md"
        approved["git_commit"] = self.wiki.publish(
            wiki_path,
            self._render_approved_wiki(approved),
            f"Approve {candidate['title']}",
        )
        approved["wiki_path"] = wiki_path
        records = []
        for claim_id in approved["claim_ids"]:
            claim = self.store.get("claim", claim_id)
            claim["review_status"] = "approved"
            claim["evidence_status"] = "supported"
            claim["reviewed_by"] = reviewer
            claim["reviewed_at"] = approved["approved_at"]
            records.append(("claim", claim))
        records.append(("candidate", approved))
        self.store.put_many(records)
        return approved

    def query(self, query: str) -> str:
        terms = [term.lower() for term in re.findall(r"\w+", query)]
        matches = []
        for candidate in self.store.list("candidate"):
            if candidate["status"] != "approved":
                continue
            content = self.wiki.read(candidate["git_commit"], candidate["wiki_path"])
            lowered = content.lower()
            if any(term in lowered for term in terms):
                matches.append(content)
        if not matches:
            raise LookupError("No approved knowledge matched the query")
        return "\n\n---\n\n".join(matches)

    def _recover_source_record(
        self, destination: Path, expected_identity: str
    ) -> Dict[str, Any]:
        manifest_path = destination / "manifest.json"
        if not manifest_path.exists():
            raise ValueError(f"Incomplete Source snapshot requires cleanup: {destination}")
        record = json.loads(manifest_path.read_text(encoding="utf-8"))
        if record.get("identity") != expected_identity:
            raise ValueError(f"Source destination identity mismatch: {destination}")
        snapshot = destination / "snapshot"
        if self._directory_hash(snapshot) != record["content_hash"]:
            raise ValueError(f"Source integrity check failed: {record['id']}")
        self.store.put("source", record)
        return record

    def _directory_hash(self, root: Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            digest.update(str(path.relative_to(root)).encode("utf-8"))
            digest.update(path.read_bytes())
        return digest.hexdigest()

    def _read_text_files(self, root: Path) -> List[Any]:
        allowed = {".md", ".txt", ".py", ".go", ".js", ".ts", ".yaml", ".yml"}
        files = []
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            if path.suffix.lower() not in allowed:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            files.append((str(path.relative_to(root)), content))
        if not files:
            raise ValueError("Source snapshot contains no supported text files")
        return files

    def _render_approved_wiki(self, candidate: Dict[str, Any]) -> str:
        authors = "\n".join(
            f"  - {json.dumps(author, ensure_ascii=False)}"
            for author in candidate["authors"]
        )
        reviewers = "\n".join(
            f"  - {json.dumps(reviewer, ensure_ascii=False)}"
            for reviewer in candidate["reviewers"]
        )
        return (
            "---\n"
            f"id: {json.dumps(candidate['id'])}\n"
            f"title: {json.dumps(candidate['title'], ensure_ascii=False)}\n"
            "type: knowledge\n"
            f"authors:\n{authors}\n"
            f"reviewers:\n{reviewers}\n"
            "status: approved\n"
            f"authority: {json.dumps(candidate['authority'])}\n"
            f"visibility: {json.dumps(candidate['visibility'])}\n"
            f"source_revision: {json.dumps(candidate['source_revision'])}\n"
            "---\n\n"
            f"{candidate['content']}"
        )
