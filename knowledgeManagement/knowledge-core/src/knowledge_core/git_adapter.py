from pathlib import Path
import subprocess
from typing import List


def run_git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


class LocalGitSourceRepository:
    def resolve(self, repository: Path, reference: str) -> str:
        return run_git(repository, "rev-parse", reference)

    def snapshot(
        self,
        repository: Path,
        revision: str,
        destination: Path,
        includes: List[str],
    ) -> None:
        tracked_files = subprocess.run(
            ["git", "-C", str(repository), "ls-tree", "-rz", "--name-only", revision],
            check=True,
            capture_output=True,
        ).stdout
        for raw_name in tracked_files.split(b"\0"):
            if not raw_name:
                continue
            relative_name = raw_name.decode("utf-8")
            if includes and not any(
                relative_name == include.rstrip("/")
                or relative_name.startswith(f"{include.rstrip('/')}/")
                for include in includes
            ):
                continue
            target_file = destination / relative_name
            target_file.parent.mkdir(parents=True, exist_ok=True)
            content = subprocess.run(
                ["git", "-C", str(repository), "show", f"{revision}:{relative_name}"],
                check=True,
                capture_output=True,
            ).stdout
            target_file.write_bytes(content)


class LocalGitWikiRepository:
    def __init__(self, repository: Path):
        self.repository = repository

    def initialize(self) -> None:
        self.repository.mkdir(parents=True, exist_ok=True)
        if (self.repository / ".git").exists():
            return
        subprocess.run(["git", "init", "-q"], cwd=self.repository, check=True)
        run_git(self.repository, "config", "user.email", "knowledge-core@example.invalid")
        run_git(self.repository, "config", "user.name", "Knowledge Core")
        (self.repository / ".gitkeep").write_text("", encoding="utf-8")
        run_git(self.repository, "add", ".gitkeep")
        run_git(self.repository, "commit", "-qm", "Initialize approved wiki")

    def publish(self, path: str, content: str, message: str) -> str:
        target = self.repository / path
        temporary = self.repository / f".{target.name}.tmp"
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)
        run_git(self.repository, "add", "--", path)
        status = run_git(self.repository, "status", "--porcelain", "--", path)
        if status:
            run_git(
                self.repository,
                "commit",
                "-m",
                message,
                "--only",
                "--",
                path,
            )
        return run_git(self.repository, "rev-parse", "HEAD")

    def read(self, commit: str, path: str) -> str:
        return run_git(self.repository, "show", f"{commit}:{path}")
