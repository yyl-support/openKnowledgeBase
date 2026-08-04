import re
from typing import Dict, List, Tuple


REQUIRED_SECTION_ORDER = (
    "一句话说明",
    "整体概述",
    "事实陈述",
    "综合推断",
    "已知限制与待确认事项",
    "来源",
)

LATIN_HEADING_RE = re.compile(r"[A-Za-z]+")
INLINE_SOURCE_RE = re.compile(r"[（(]来源[:：]")
NUMBER_RE = re.compile(r"(?<![\w-])\d+(?:\.\d+)?%?")
MERMAID_START_RE = re.compile(
    r"^(?:graph|flowchart|sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|"
    r"erDiagram|journey|gantt|pie|mindmap|timeline|gitGraph|C4\w*)\b"
)


def validate_wiki_contract(content: str) -> None:
    """Validate generated Wiki Markdown before a candidate is persisted."""
    lines = content.splitlines()
    h1_count = sum(1 for line in lines if line.startswith("# "))
    if h1_count != 1:
        raise ValueError(f"Wiki must contain exactly one H1 heading, found {h1_count}")
    if "---" not in content:
        raise ValueError("Wiki must use --- separators between sections")

    sections = _sections(lines)
    if not sections:
        raise ValueError("Wiki must contain ## section headings")
    _validate_heading_language(sections)
    _validate_section_order(sections)
    _validate_fact_presentation(sections)
    _validate_tables(lines)
    _validate_mermaid(lines)


def _sections(lines: List[str]) -> List[Tuple[str, List[str]]]:
    sections = []
    current = None
    body = []
    for line in lines:
        if line.startswith("## "):
            if current is not None:
                sections.append((current, body))
            current = line[3:].strip()
            body = []
        elif current is not None:
            body.append(line)
    if current is not None:
        sections.append((current, body))
    return sections


def _section_name(heading: str) -> str:
    return re.sub(r"^[一二三四五六七八九十]+[、.]\s*", "", heading).strip()


def _validate_heading_language(sections: List[Tuple[str, List[str]]]) -> None:
    for heading, _ in sections:
        for word in LATIN_HEADING_RE.findall(heading):
            if word.isupper() or re.match(r"^[A-Z][a-z]+$", word):
                continue
            raise ValueError(
                f"Wiki heading mixes Latin words not allowed by contract: ## {heading}"
            )


def _validate_section_order(sections: List[Tuple[str, List[str]]]) -> None:
    names = [_section_name(heading) for heading, _ in sections]
    if "三十秒概览" in names:
        raise ValueError("Wiki must use 整体概述 instead of 三十秒概览")
    missing = [name for name in REQUIRED_SECTION_ORDER if name not in names]
    if missing:
        raise ValueError(f"Wiki is missing required heading: {missing[0]}")
    positions = [names.index(name) for name in REQUIRED_SECTION_ORDER]
    if positions != sorted(positions):
        raise ValueError("Wiki required sections are not in the required order")
    if names[-1] != "构建信息":
        raise ValueError("Wiki 构建信息 section must be the final section")


def _validate_fact_presentation(sections: List[Tuple[str, List[str]]]) -> None:
    section_map: Dict[str, List[str]] = {
        _section_name(heading): body for heading, body in sections
    }
    for line in section_map["事实陈述"]:
        if INLINE_SOURCE_RE.search(line):
            raise ValueError(
                "Wiki facts must not contain inline source annotations; keep traceability in metadata"
            )
        if line.lstrip().startswith("- ") and len(NUMBER_RE.findall(line)) >= 3:
            raise ValueError(
                "Wiki data-heavy facts must use a Markdown table instead of a list item"
            )


def _validate_tables(lines: List[str]) -> None:
    for index, line in enumerate(lines):
        if not _is_table_separator(line):
            continue
        if index == 0 or not _is_table_row(lines[index - 1]):
            raise ValueError("Markdown table separator must follow a header row")
        columns = _table_columns(line)
        if columns < 2 or _table_columns(lines[index - 1]) != columns:
            raise ValueError("Markdown table header and separator column counts must match")
        row_index = index + 1
        while row_index < len(lines) and _is_table_row(lines[row_index]):
            if _table_columns(lines[row_index]) != columns:
                raise ValueError("Markdown table rows must use a consistent column count")
            row_index += 1


def _is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return len(cells) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def _table_columns(line: str) -> int:
    return len(line.strip().strip("|").split("|"))


def _validate_mermaid(lines: List[str]) -> None:
    in_mermaid = False
    diagram_lines = []
    for line in lines:
        if not in_mermaid and line.strip() == "```mermaid":
            in_mermaid = True
            diagram_lines = []
            continue
        if in_mermaid and line.strip() == "```":
            meaningful = [item.strip() for item in diagram_lines if item.strip()]
            if not meaningful or not MERMAID_START_RE.match(meaningful[0]):
                raise ValueError("Mermaid block must start with a supported diagram declaration")
            in_mermaid = False
            continue
        if in_mermaid:
            diagram_lines.append(line)
    if in_mermaid:
        raise ValueError("Mermaid code block is not closed")
