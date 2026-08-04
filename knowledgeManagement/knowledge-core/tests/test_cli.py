import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class KnowledgeCliTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.repository = self.root / "demo-repository"
        self.workspace = self.root / "workspace"
        self._create_repository()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_repository(self):
        self.repository.mkdir()
        (self.repository / "README.md").write_text(
            "# Demo Scheduler\n\n"
            "Demo Scheduler assigns queued jobs\n"
            "to available worker nodes.\n\n"
            "## Components\n\n"
            "- API accepts jobs.\n"
            "- Scheduler selects a worker.\n",
            encoding="utf-8",
        )
        (self.repository / "scheduler.py").write_text(
            "def choose_worker(workers):\n"
            "    return next(worker for worker in workers if worker['available'])\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q"], cwd=self.repository, check=True)
        subprocess.run(
            ["git", "config", "user.email", "fixture@example.invalid"],
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Fixture"],
            cwd=self.repository,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=self.repository, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "Initial fixture"],
            cwd=self.repository,
            check=True,
        )

    def run_cli(self, *arguments, expected_returncode=0):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "knowledge_core.cli",
                "--workspace",
                str(self.workspace),
                "--output-dir",
                str(self.workspace / "output"),
                *arguments,
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(
            expected_returncode,
            result.returncode,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def model_config(self, base_url):
        path = self.root / "models.json"
        path.write_text(
            json.dumps(
                {
                    "profiles": {
                        "fake-deepseek": {
                            "adapter": "openai-compatible",
                            "base_url": base_url,
                            "model": "deepseek-v4-flash",
                            "api_key_env": "TEST_MODEL_API_KEY",
                            "timeout_seconds": 5,
                            "max_claims": 20,
                            "max_tokens": 4096,
                            "thinking": "disabled",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_user_can_build_review_publish_and_query_a_git_source(self):
        self.run_cli("init")

        source = json.loads(
            self.run_cli(
                "source",
                "add-git",
                "--repo",
                str(self.repository),
                "--ref",
                "HEAD",
                "--title",
                "Demo Scheduler",
            ).stdout
        )
        self.assertEqual("public", source["visibility"])
        self.assertEqual("active", source["status"])

        normalized = json.loads(
            self.run_cli("normalize", "--source", source["id"]).stdout
        )
        self.assertEqual(source["revision"], normalized["source_revision"])
        self.assertIn("Demo Scheduler", normalized["content"])

        claims = json.loads(
            self.run_cli(
                "claims",
                "extract",
                "--normalized",
                normalized["id"],
                "--model",
                "deterministic",
            ).stdout
        )
        self.assertGreaterEqual(len(claims), 2)
        self.assertTrue(
            all(claim["review_status"] == "pending-review" for claim in claims)
        )
        self.assertTrue(all(claim["source_refs"] for claim in claims))
        source_paths = {
            claim["source_refs"][0]["machine_locator"]["path"] for claim in claims
        }
        self.assertEqual({"README.md", "scheduler.py"}, source_paths)

        candidate = json.loads(
            self.run_cli(
                "wiki",
                "build",
                "--source",
                source["id"],
                "--model",
                "deterministic",
            ).stdout
        )
        self.assertEqual("pending-review", candidate["status"])
        self.assertIn("## 二、整体概述", candidate["content"])
        self.assertIn("## 六、来源", candidate["content"])
        self.assertTrue(candidate["content"].rstrip().endswith(f"Source：{source['human_location']}"))

        before_approval = self.run_cli(
            "query", "Demo Scheduler", expected_returncode=2
        )
        self.assertIn("No approved knowledge", before_approval.stderr)

        approved = json.loads(
            self.run_cli(
                "review",
                "approve",
                "--candidate",
                candidate["id"],
                "--reviewer",
                "human-test-reviewer",
            ).stdout
        )
        self.assertEqual("approved", approved["status"])
        self.assertTrue(approved["git_commit"])
        approved_claims = json.loads(
            self.run_cli(
                "claims", "list", "--source", source["id"]
            ).stdout
        )
        self.assertTrue(
            all(claim["review_status"] == "approved" for claim in approved_claims)
        )
        self.assertTrue(
            all(claim["evidence_status"] == "supported" for claim in approved_claims)
        )

        wiki_file = (
            self.workspace
            / "output"
            / f"Demo-Scheduler--{source['id'].removeprefix('source-git-')}.md"
        )
        self.assertTrue(wiki_file.exists())
        self.assertIn("status: approved", wiki_file.read_text(encoding="utf-8"))

        query = self.run_cli("query", "worker nodes")
        self.assertIn("Demo Scheduler", query.stdout)
        self.assertIn("Source:", query.stdout)

        rogue = self.workspace / "output" / "rogue.md"
        rogue.write_text("# Demo Scheduler rogue pending content", encoding="utf-8")
        query_after_rogue_file = self.run_cli("query", "Demo Scheduler")
        self.assertNotIn("rogue pending content", query_after_rogue_file.stdout)

    def test_reingesting_same_revision_is_idempotent(self):
        self.run_cli("init")
        arguments = (
            "source",
            "add-git",
            "--repo",
            str(self.repository),
            "--ref",
            "HEAD",
            "--title",
            "Demo Scheduler",
        )
        first = json.loads(self.run_cli(*arguments).stdout)
        second = json.loads(self.run_cli(*arguments).stdout)

        self.assertEqual(first["id"], second["id"])
        sources = list((self.workspace / "sources").iterdir())
        self.assertEqual(1, len(sources))

    def test_git_source_can_be_scoped_to_a_subdirectory(self):
        (self.repository / "report").mkdir()
        (self.repository / "report" / "guide.md").write_text(
            "# Report Guide\n\nOnly this report should enter the Source.\n",
            encoding="utf-8",
        )
        (self.repository / "report" / "中文指南.md").write_text(
            "# 中文指南\n\n中文文件也必须进入 Source。\n",
            encoding="utf-8",
        )
        (self.repository / "outside.md").write_text(
            "# Outside\n\nThis file must not enter the Source.\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "."], cwd=self.repository, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "Add scoped fixture"],
            cwd=self.repository,
            check=True,
        )
        self.run_cli("init")

        source = json.loads(
            self.run_cli(
                "source",
                "add-git",
                "--repo",
                str(self.repository),
                "--ref",
                "HEAD",
                "--canonical-url",
                "https://github.com/example/demo-scheduler",
                "--include",
                "report/",
                "--title",
                "Scoped Reports",
            ).stdout
        )

        self.assertEqual(["report/"], source["scope"]["includes"])
        self.assertEqual(
            "https://github.com/example/demo-scheduler", source["canonical_url"]
        )
        self.assertIn("github.com/example/demo-scheduler", source["human_location"])
        snapshot = self.workspace / "sources" / source["id"] / "snapshot"
        self.assertTrue((snapshot / "report" / "guide.md").exists())
        self.assertTrue((snapshot / "report" / "中文指南.md").exists())
        self.assertFalse((snapshot / "README.md").exists())
        self.assertFalse((snapshot / "outside.md").exists())

        unscoped = json.loads(
            self.run_cli(
                "source",
                "add-git",
                "--repo",
                str(self.repository),
                "--ref",
                "HEAD",
                "--canonical-url",
                "https://github.com/example/demo-scheduler",
                "--title",
                "Scoped Reports",
            ).stdout
        )
        self.assertNotEqual(source["id"], unscoped["id"])

    def test_tampered_source_snapshot_blocks_normalization(self):
        self.run_cli("init")
        source = json.loads(
            self.run_cli(
                "source",
                "add-git",
                "--repo",
                str(self.repository),
                "--title",
                "Demo Scheduler",
            ).stdout
        )
        snapshot_readme = (
            self.workspace / "sources" / source["id"] / "snapshot" / "README.md"
        )
        snapshot_readme.write_text("tampered", encoding="utf-8")

        result = self.run_cli(
            "normalize", "--source", source["id"], expected_returncode=2
        )
        self.assertIn("integrity check failed", result.stderr)

    def test_tampering_after_normalization_blocks_all_downstream_stages(self):
        self.run_cli("init")
        source = json.loads(
            self.run_cli(
                "source",
                "add-git",
                "--repo",
                str(self.repository),
                "--title",
                "Demo Scheduler",
            ).stdout
        )
        normalized = json.loads(
            self.run_cli("normalize", "--source", source["id"]).stdout
        )
        snapshot_readme = (
            self.workspace / "sources" / source["id"] / "snapshot" / "README.md"
        )
        snapshot_readme.write_text("tampered after normalization", encoding="utf-8")

        extract = self.run_cli(
            "claims",
            "extract",
            "--normalized",
            normalized["id"],
            "--model",
            "deterministic",
            expected_returncode=2,
        )
        self.assertIn("integrity check failed", extract.stderr)
        listed = self.run_cli(
            "claims",
            "list",
            "--source",
            source["id"],
            expected_returncode=2,
        )
        self.assertIn("integrity check failed", listed.stderr)

    def test_same_title_sources_publish_to_distinct_wiki_pages(self):
        self.run_cli("init")
        second_repository = self.root / "second-repository"
        subprocess.run(
            ["git", "clone", "-q", str(self.repository), str(second_repository)],
            check=True,
        )
        (second_repository / "README.md").write_text(
            "# Demo Scheduler\n\nSecond implementation uses a priority queue.\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "config", "user.email", "fixture@example.invalid"],
            cwd=second_repository,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Fixture"],
            cwd=second_repository,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=second_repository, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "Second fixture"],
            cwd=second_repository,
            check=True,
        )

        sources = []
        for repository in (self.repository, second_repository):
            source = json.loads(
                self.run_cli(
                    "source",
                    "add-git",
                    "--repo",
                    str(repository),
                    "--title",
                    "Demo Scheduler",
                ).stdout
            )
            normalized = json.loads(
                self.run_cli("normalize", "--source", source["id"]).stdout
            )
            self.run_cli(
                "claims",
                "extract",
                "--normalized",
                normalized["id"],
                "--model",
                "deterministic",
            )
            candidate = json.loads(
                self.run_cli(
                    "wiki",
                    "build",
                    "--source",
                    source["id"],
                    "--model",
                    "deterministic",
                ).stdout
            )
            self.run_cli(
                "review",
                "approve",
                "--candidate",
                candidate["id"],
                "--reviewer",
                "human-test-reviewer",
            )
            sources.append(source)

        pages = list((self.workspace / "output").glob("Demo-Scheduler--*.md"))
        self.assertEqual(2, len(pages))

    def test_openai_compatible_profile_extracts_claims_and_builds_wiki(self):
        responses = [
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "claims": [
                                        {
                                            "statement": "Demo Scheduler assigns jobs to worker nodes.",
                                            "claim_type": "fact",
                                            "path": "README.md",
                                            "block_id": "b1",
                                        }
                                    ]
                                }
                            )
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "content": (
                                        "# Demo Scheduler\n\n"
                                        "> ⚠️ 未审核候选知识。\n\n"
                                        "---\n\n"
                                        "## 一、一句话说明\n\n"
                                        "Schedules jobs.\n\n"
                                        "---\n\n"
                                        "## 二、整体概述\n\n"
                                        "- Assigns jobs.\n\n"
                                        "---\n\n"
                                        "## 三、事实陈述\n\n"
                                        "- Assigns jobs.\n\n"
                                        "---\n\n"
                                        "## 四、综合推断\n\n"
                                        "- None.\n\n"
                                        "---\n\n"
                                        "## 五、已知限制与待确认事项\n\n"
                                        "- All supplied claims are pending review.\n\n"
                                        "---\n\n"
                                        "## 六、来源\n\n"
                                        "- README.md\n\n"
                                        "---\n\n"
                                        "## 七、构建信息\n\n"
                                        "- Source：demo\n"
                                    )
                                }
                            )
                        }
                    }
                ]
            },
        ]

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                request = json.loads(self.rfile.read(length))
                self.server.requests.append(request)
                payload = responses.pop(0)
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        server.requests = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        config = self.model_config(f"http://127.0.0.1:{server.server_port}")
        instruction_file = self.root / "regeneration.md"
        instruction_file.write_text(
            "选择能独立支持陈述的最小连续行范围。", encoding="utf-8"
        )
        os.environ["TEST_MODEL_API_KEY"] = "test-secret"
        try:
            self.run_cli("init")
            source = json.loads(
                self.run_cli(
                    "--model-config",
                    str(config),
                    "source",
                    "add-git",
                    "--repo",
                    str(self.repository),
                    "--title",
                    "Demo Scheduler",
                ).stdout
            )
            normalized = json.loads(
                self.run_cli(
                    "--model-config",
                    str(config),
                    "normalize",
                    "--source",
                    source["id"],
                ).stdout
            )
            claims = json.loads(
                self.run_cli(
                    "--model-config",
                    str(config),
                    "claims",
                    "extract",
                    "--normalized",
                    normalized["id"],
                    "--model",
                    "fake-deepseek",
                    "--instruction-file",
                    str(instruction_file),
                ).stdout
            )
            candidate = json.loads(
                self.run_cli(
                    "--model-config",
                    str(config),
                    "wiki",
                    "build",
                    "--source",
                    source["id"],
                    "--model",
                    "fake-deepseek",
                    "--instruction-file",
                    str(instruction_file),
                ).stdout
            )
        finally:
            server.shutdown()
            server.server_close()
            os.environ.pop("TEST_MODEL_API_KEY", None)

        self.assertEqual(1, len(claims))
        locator = claims[0]["source_refs"][0]["machine_locator"]
        self.assertEqual("README.md", locator["path"])
        self.assertEqual(1, locator["line_start"])
        self.assertEqual(
            "# Demo Scheduler\n\nDemo Scheduler assigns queued jobs\nto available worker nodes.",
            claims[0]["source_refs"][0]["evidence_quote"],
        )
        self.assertEqual("b1", claims[0]["source_refs"][0]["machine_locator"]["block_id"])
        self.assertIn("## 二、整体概述", candidate["content"])
        self.assertEqual(2, len(server.requests))
        self.assertEqual("deepseek-v4-flash", server.requests[0]["model"])
        self.assertEqual({"type": "json_object"}, server.requests[0]["response_format"])
        self.assertEqual(4096, server.requests[0]["max_tokens"])
        self.assertEqual({"type": "disabled"}, server.requests[0]["thinking"])
        self.assertIn(
            "选择能独立支持陈述的最小连续行范围。",
            server.requests[0]["messages"][1]["content"],
        )
        self.assertIn(
            "选择能独立支持陈述的最小连续行范围。",
            server.requests[1]["messages"][1]["content"],
        )
        self.assertRegex(claims[0]["generation_instruction_hash"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            claims[0]["generation_instruction_hash"],
            candidate["generation_instruction_hash"],
        )

    def test_model_claim_with_unknown_block_is_rejected(self):
        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "claims": [
                                    {
                                        "statement": "The project uses PostgreSQL.",
                                        "claim_type": "fact",
                                        "path": "README.md",
                                        "block_id": "b999",
                                    }
                                ]
                            }
                        )
                    }
                }
            ]
        }
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                self.rfile.read(length)
                body = json.dumps(response).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        config = self.model_config(f"http://127.0.0.1:{server.server_port}")
        os.environ["TEST_MODEL_API_KEY"] = "test-secret"
        try:
            self.run_cli("init")
            source = json.loads(
                self.run_cli(
                    "--model-config",
                    str(config),
                    "source",
                    "add-git",
                    "--repo",
                    str(self.repository),
                    "--title",
                    "Demo Scheduler",
                ).stdout
            )
            normalized = json.loads(
                self.run_cli(
                    "--model-config",
                    str(config),
                    "normalize",
                    "--source",
                    source["id"],
                ).stdout
            )
            result = self.run_cli(
                "--model-config",
                str(config),
                "claims",
                "extract",
                "--normalized",
                normalized["id"],
                "--model",
                "fake-deepseek",
                expected_returncode=2,
            )
        finally:
            server.shutdown()
            server.server_close()
            os.environ.pop("TEST_MODEL_API_KEY", None)

        self.assertIn("unknown block", result.stderr)
        claims_path = self.workspace / "claims" / f"{normalized['id']}.json"
        self.assertFalse(claims_path.exists())

    def test_model_claim_without_lexical_overlap_is_rejected(self):
        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "claims": [
                                    {
                                        "statement": "The project uses PostgreSQL.",
                                        "claim_type": "fact",
                                        "path": "README.md",
                                        "block_id": "b1",
                                    }
                                ]
                            }
                        )
                    }
                }
            ]
        }

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                self.rfile.read(length)
                body = json.dumps(response).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        config = self.model_config(f"http://127.0.0.1:{server.server_port}")
        os.environ["TEST_MODEL_API_KEY"] = "test-secret"
        try:
            self.run_cli("init")
            source = json.loads(
                self.run_cli(
                    "--model-config",
                    str(config),
                    "source",
                    "add-git",
                    "--repo",
                    str(self.repository),
                    "--title",
                    "Demo Scheduler",
                ).stdout
            )
            normalized = json.loads(
                self.run_cli(
                    "--model-config",
                    str(config),
                    "normalize",
                    "--source",
                    source["id"],
                ).stdout
            )
            result = self.run_cli(
                "--model-config",
                str(config),
                "claims",
                "extract",
                "--normalized",
                normalized["id"],
                "--model",
                "fake-deepseek",
                expected_returncode=2,
            )
        finally:
            server.shutdown()
            server.server_close()
            os.environ.pop("TEST_MODEL_API_KEY", None)

        self.assertIn("no lexical overlap", result.stderr)
        claims_path = self.workspace / "claims" / f"{normalized['id']}.json"
        self.assertFalse(claims_path.exists())

    def test_wiki_with_mixed_language_heading_is_rejected(self):
        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "content": (
                                    "# Demo Scheduler\n\n"
                                    "> ⚠️ 未审核候选知识。\n\n"
                                    "---\n\n"
                                    "## 支撑 claim 清单\n\n"
                                    "Mixed heading.\n\n"
                                    "---\n\n"
                                    "## 一句话说明\n\n"
                                    "Schedules jobs.\n\n"
                                    "---\n\n"
                                    "## 整体概述\n\n"
                                    "- Assigns jobs.\n\n"
                                    "---\n\n"
                                    "## 事实陈述\n\n"
                                    "- Assigns jobs.\n\n"
                                    "---\n\n"
                                    "## 综合推断\n\n"
                                    "- None.\n\n"
                                    "---\n\n"
                                    "## 已知限制与待确认事项\n\n"
                                    "- All pending.\n\n"
                                    "---\n\n"
                                    "## 来源\n\n"
                                    "- README.md\n"
                                )
                            }
                        )
                    }
                }
            ]
        }

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                self.rfile.read(length)
                body = json.dumps(response).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        config = self.model_config(f"http://127.0.0.1:{server.server_port}")
        os.environ["TEST_MODEL_API_KEY"] = "test-secret"
        try:
            self.run_cli("init")
            source = json.loads(
                self.run_cli(
                    "--model-config",
                    str(config),
                    "source",
                    "add-git",
                    "--repo",
                    str(self.repository),
                    "--title",
                    "Demo Scheduler",
                ).stdout
            )
            normalized = json.loads(
                self.run_cli(
                    "--model-config",
                    str(config),
                    "normalize",
                    "--source",
                    source["id"],
                ).stdout
            )
            self.run_cli(
                "--model-config",
                str(config),
                "claims",
                "extract",
                "--normalized",
                normalized["id"],
                "--model",
                "deterministic",
            )
            result = self.run_cli(
                "--model-config",
                str(config),
                "wiki",
                "build",
                "--source",
                source["id"],
                "--model",
                "fake-deepseek",
                expected_returncode=2,
            )
        finally:
            server.shutdown()
            server.server_close()
            os.environ.pop("TEST_MODEL_API_KEY", None)

        self.assertIn("mixes Latin words", result.stderr)
        candidate_path = self.workspace / "candidates"
        self.assertFalse(any(candidate_path.glob("*.json")))

    def test_wiki_validate_rejects_old_section_order_and_inline_sources(self):
        self.run_cli("init")
        old_order = self.root / "old-order.md"
        old_order.write_text(
            self._valid_wiki().replace(
                "## 二、整体概述", "## 二、三十秒概览"
            ),
            encoding="utf-8",
        )
        result = self.run_cli(
            "wiki", "validate", "--file", str(old_order), expected_returncode=2
        )
        self.assertIn("整体概述", result.stderr)

        inline_source = self.root / "inline-source.md"
        inline_source.write_text(
            self._valid_wiki().replace(
                "- Scheduler assigns jobs.",
                "- Scheduler assigns jobs.（来源：README.md, block b1, lines 1-5）",
            ),
            encoding="utf-8",
        )
        result = self.run_cli(
            "wiki", "validate", "--file", str(inline_source), expected_returncode=2
        )
        self.assertIn("inline source", result.stderr)

    def test_wiki_validate_checks_tables_and_mermaid(self):
        self.run_cli("init")
        valid = self.root / "valid.md"
        valid.write_text(self._valid_wiki(), encoding="utf-8")
        result = json.loads(
            self.run_cli("wiki", "validate", "--file", str(valid)).stdout
        )
        self.assertEqual("valid", result["status"])

        dense_data = self.root / "dense-data.md"
        dense_data.write_text(
            self._valid_wiki().replace(
                "- Scheduler assigns jobs.",
                "- Go 160, Python 75, Java 23.",
            ),
            encoding="utf-8",
        )
        result = self.run_cli(
            "wiki", "validate", "--file", str(dense_data), expected_returncode=2
        )
        self.assertIn("Markdown table", result.stderr)

        invalid_mermaid = self.root / "invalid-mermaid.md"
        invalid_mermaid.write_text(
            self._valid_wiki().replace(
                "flowchart LR", "not-a-diagram"
            ),
            encoding="utf-8",
        )
        result = self.run_cli(
            "wiki", "validate", "--file", str(invalid_mermaid), expected_returncode=2
        )
        self.assertIn("Mermaid block", result.stderr)

    def _valid_wiki(self):
        return (
            "> 未审核候选知识。\n\n"
            "# Demo Scheduler\n\n"
            "---\n\n"
            "## 一、一句话说明\n\n"
            "Scheduler assigns jobs.\n\n"
            "---\n\n"
            "## 二、整体概述\n\n"
            "| 指标 | 数量 |\n"
            "|---|---:|\n"
            "| Workers | 3 |\n\n"
            "```mermaid\n"
            "flowchart LR\n"
            "    API --> Scheduler\n"
            "```\n\n"
            "---\n\n"
            "## 三、事实陈述\n\n"
            "- Scheduler assigns jobs.\n\n"
            "---\n\n"
            "## 四、综合推断\n\n"
            "- No additional inference.\n\n"
            "---\n\n"
            "## 五、已知限制与待确认事项\n\n"
            "- All claims await review.\n\n"
            "---\n\n"
            "## 六、来源\n\n"
            "- README.md\n\n"
            "---\n\n"
            "## 七、构建信息\n\n"
            "- Source: demo\n"
        )



if __name__ == "__main__":
    unittest.main()
