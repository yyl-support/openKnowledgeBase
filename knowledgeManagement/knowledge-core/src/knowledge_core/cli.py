import argparse
import json
from pathlib import Path
import subprocess
import sys

from .application import KnowledgeApplication
from .git_adapter import LocalGitSourceRepository, LocalGitWikiRepository
from .model import ConfiguredModelRegistry
from .store import MetadataStore


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="knowledge")
    root.add_argument("--workspace", type=Path, required=True)
    root.add_argument("--output-dir", type=Path, default=Path("output"))
    root.add_argument("--model-config", type=Path)
    commands = root.add_subparsers(dest="command", required=True)

    commands.add_parser("init")

    source = commands.add_parser("source")
    source_commands = source.add_subparsers(dest="source_command", required=True)
    add_git = source_commands.add_parser("add-git")
    add_git.add_argument("--repo", type=Path, required=True)
    add_git.add_argument("--ref", default="HEAD")
    add_git.add_argument("--title", required=True)
    add_git.add_argument("--include", action="append", default=[])
    add_git.add_argument("--canonical-url")

    normalize = commands.add_parser("normalize")
    normalize.add_argument("--source", required=True)

    claims = commands.add_parser("claims")
    claim_commands = claims.add_subparsers(dest="claims_command", required=True)
    extract = claim_commands.add_parser("extract")
    extract.add_argument("--normalized", required=True)
    extract.add_argument("--model", required=True)
    extract.add_argument("--instruction-file", type=Path)
    list_claims = claim_commands.add_parser("list")
    list_claims.add_argument("--source", required=True)

    wiki = commands.add_parser("wiki")
    wiki_commands = wiki.add_subparsers(dest="wiki_command", required=True)
    build = wiki_commands.add_parser("build")
    build.add_argument("--source", required=True)
    build.add_argument("--model", required=True)
    build.add_argument("--instruction-file", type=Path)
    validate = wiki_commands.add_parser("validate")
    validate.add_argument("--file", type=Path, required=True)

    review = commands.add_parser("review")
    review_commands = review.add_subparsers(dest="review_command", required=True)
    approve = review_commands.add_parser("approve")
    approve.add_argument("--candidate", required=True)
    approve.add_argument("--reviewer", required=True)

    query = commands.add_parser("query")
    query.add_argument("text")
    return root


def execute(arguments: argparse.Namespace):
    application = KnowledgeApplication(
        workspace=arguments.workspace,
        store=MetadataStore(arguments.workspace),
        models=ConfiguredModelRegistry(arguments.model_config),
        git_sources=LocalGitSourceRepository(),
        wiki=LocalGitWikiRepository(arguments.output_dir),
    )
    if arguments.command == "init":
        return application.initialize()
    if arguments.command == "source" and arguments.source_command == "add-git":
        return application.add_git_source(
            arguments.repo,
            arguments.ref,
            arguments.title,
            arguments.include,
            arguments.canonical_url,
        )
    if arguments.command == "normalize":
        return application.normalize(arguments.source)
    if arguments.command == "claims" and arguments.claims_command == "extract":
        return application.extract_claims(
            arguments.normalized, arguments.model, arguments.instruction_file
        )
    if arguments.command == "claims" and arguments.claims_command == "list":
        return application.list_claims(arguments.source)
    if arguments.command == "wiki" and arguments.wiki_command == "build":
        return application.build_wiki_candidate(
            arguments.source, arguments.model, arguments.instruction_file
        )
    if arguments.command == "wiki" and arguments.wiki_command == "validate":
        return application.validate_wiki_file(arguments.file)
    if arguments.command == "review" and arguments.review_command == "approve":
        return application.approve_candidate(arguments.candidate, arguments.reviewer)
    if arguments.command == "query":
        return application.query(arguments.text)
    raise ValueError("Unsupported command")


def main() -> int:
    arguments = parser().parse_args()
    try:
        result = execute(arguments)
    except (
        KeyError,
        LookupError,
        OSError,
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        print(str(error), file=sys.stderr)
        return 2
    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
