from pathlib import Path
from typing import Any, Dict, List, Protocol


class MetadataRepository(Protocol):
    def initialize(self) -> None: ...
    def put(self, kind: str, record: Dict[str, Any]) -> Dict[str, Any]: ...
    def put_many(self, records: List[Any]) -> None: ...
    def get(self, kind: str, record_id: str) -> Dict[str, Any]: ...
    def find_one(
        self, kind: str, field: str, value: str
    ) -> Dict[str, Any]: ...
    def list(self, kind: str) -> List[Dict[str, Any]]: ...


class KnowledgeModel(Protocol):
    name: str

    def extract_claims(
        self, normalized: Dict[str, Any], instructions: str = ""
    ) -> List[Dict[str, Any]]: ...

    def build_wiki(
        self,
        source: Dict[str, Any],
        claims: List[Dict[str, Any]],
        instructions: str = "",
    ) -> str: ...


class ModelRegistry(Protocol):
    def get(self, name: str) -> KnowledgeModel: ...


class GitSourceRepository(Protocol):
    def resolve(self, repository: Path, reference: str) -> str: ...
    def snapshot(
        self,
        repository: Path,
        revision: str,
        destination: Path,
        includes: List[str],
    ) -> None: ...


class WikiRepository(Protocol):
    def initialize(self) -> None: ...
    def publish(self, path: str, content: str, message: str) -> str: ...
    def read(self, commit: str, path: str) -> str: ...
