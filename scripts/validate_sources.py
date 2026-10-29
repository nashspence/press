#!/usr/bin/env python3
"""Check every tracked Markdown source against FORMAT.md.

Uses Pandoc's GFM reader, and intentionally avoids rewriting any manuscript.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

SOURCE_EXTENSIONS = {".md", ".markdown"}
PANDOC_READER = "gfm+tex_math_dollars+raw_html"
ANCHOR = re.compile(
    r"^\s*<a\s+(?:id|name)=['\"]([a-z][a-z0-9]*(?:-[a-z0-9]+)*)['\"]\s*>\s*</a>\s*$",
)
ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE_START = re.compile(r"^ {0,3}(`{3,}|~{3,})")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def report(path: Path, problem: str, line: int | None = None) -> str:
    return f"{path}:{line}: {problem}" if line is not None else f"{path}: {problem}"


def visible_lines(source: str) -> list[tuple[int, str]]:
    """Mask fenced and indented code, which are not prose/heading syntax."""
    visible = []
    fence_char = ""
    fence_length = 0
    for n, line in enumerate(source.splitlines(), start=1):
        if fence_char:
            if re.fullmatch(r" {0,3}" + re.escape(fence_char) + "{" + str(fence_length) + r",}\s*", line):
                fence_char = ""
                fence_length = 0
            visible.append((n, ""))
            continue
        fence = FENCE_START.match(line)
        if fence:
            fence_char = fence.group(1)[0]
            fence_length = len(fence.group(1))
            visible.append((n, ""))
            continue
        # Indented code is not prose, but a bullet with indentation may be.
        visible.append((n, "" if line.startswith("    ") else line))
    return visible


def walk(obj):
    if isinstance(obj, dict):
        if "t" in obj:
            yield obj
        for item in obj.values():
            yield from walk(item)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk(item)


def inline_text(inlines) -> str:
    text = []
    for node in walk(inlines):
        if node["t"] == "Str":
            text.append(node.get("c", ""))
        elif node["t"] in ("Code", "Math"):
            content = node.get("c", [])
            if isinstance(content, list) and len(content) > 1:
                text.append(str(content[1]))
    return "".join(text)


def validate_text(path: Path, raw: bytes, manuscript: bool) -> tuple[str | None, set[str], list[str]]:
    errors: list[str] = []
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        return None, set(), [report(path, f"not valid UTF-8: {exc}")]
    if source.startswith("\ufeff"):
        errors.append(report(path, "UTF-8 BOM is prohibited"))
    if "\r" in source:
        errors.append(report(path, "use LF line endings (CR/CRLF found)"))
    if source and not source.endswith("\n"):
        errors.append(report(path, "file must end with a newline"))
    if unicodedata.normalize("NFC", source) != source:
        errors.append(report(path, "text must use Unicode NFC normalization"))
    for n, line in enumerate(source.splitlines(), start=1):
        if any((ord(ch) < 32 and ch not in "\t\n\r") or ord(ch) == 127 for ch in line):
            errors.append(report(path, "non-text control character", n))
    lines = visible_lines(source)
    anchors: set[str] = set()
    heading_levels: list[tuple[int, int]] = []
    for i, (line_no, line) in enumerate(lines):
        anchor = ANCHOR.fullmatch(line)
        if anchor:
            slug = anchor.group(1)
            if slug in anchors:
                errors.append(report(path, f"duplicate explicit anchor #{slug}", line_no))
            anchors.add(slug)
        heading = ATX_HEADING.match(line)
        if not heading:
            continue
        level = len(heading.group(1))
        heading_levels.append((line_no, level))
        if manuscript and level > 1:
            j = i - 1
            while j >= 0 and not lines[j][1].strip() and i - j <= 2:
                j -= 1
            if j < 0 or not ANCHOR.fullmatch(lines[j][1]):
                errors.append(report(path, f'level-{level} heading needs a preceding <a id="stable-id"></a>', line_no))
    if manuscript:
        title_lines = [n for n, level in heading_levels if level == 1]
        if len(title_lines) != 1:
            errors.append(report(path, f"manuscript needs exactly one ATX # title; found {len(title_lines)}"))
        elif heading_levels and heading_levels[0][1] != 1:
            errors.append(report(path, "first heading in manuscript must be # title", heading_levels[0][0]))
        previous_level = 0
        for n, level in heading_levels:
            if previous_level and level > previous_level + 1:
                errors.append(report(path, f"skipped heading level: H{previous_level} to H{level}", n))
            previous_level = level
        display_open: int | None = None
        for n, line in lines:
            # Inline code is literal, not a math delimiter.
            prose = re.sub(r"(`+).*?\1", "", line)
            prose = prose.replace(r"\$", "")
            if "$$" in prose and prose.strip() != "$$":
                errors.append(report(path, "display-math $$ must be alone on its line", n))
            if prose.strip() == "$$":
                display_open = None if display_open is not None else n
        if display_open is not None:
            errors.append(report(path, "unclosed display-math $$ delimiter", display_open))
    return source, anchors, errors


def pandoc_ast(path: Path, pandoc: str) -> tuple[dict | None, list[str]]:
    cmd = [pandoc, "--from", PANDOC_READER, "--to", "json", str(path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None, [report(path, f"Pandoc not found: {pandoc}")]
    if result.returncode:
        return None, [report(path, "Pandoc could not parse GFM: " + result.stderr.strip())]
    try:
        return json.loads(result.stdout), []
    except json.JSONDecodeError as exc:
        return None, [report(path, f"Pandoc returned invalid JSON: {exc}")]


def validate_repository(root: Path, paths: list[Path], pandoc: str = "pandoc") -> list[str]:
    """Validate all given repo-relative Markdown files. No network calls."""
    root = root.resolve()
    errors: list[str] = []
    metadata: dict[Path, dict] = {}
    for rel in paths:
        rel = Path(rel)
        if rel.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        path = root / rel
        if not path.is_file():
            errors.append(report(rel, "tracked Markdown source does not exist"))
            continue
        manuscript = len(rel.parts) == 3 and rel.parts[0] == "works" and rel.parts[2] == "manuscript.md"
        if manuscript and not SLUG.fullmatch(rel.parts[1]):
            errors.append(report(rel, "work slug must be lowercase hyphen-separated ASCII"))
        source, explicit_ids, text_errors = validate_text(rel, path.read_bytes(), manuscript)
        errors.extend(text_errors)
        if source is None:
            continue
        ast, parse_errors = pandoc_ast(path, pandoc)
        errors.extend(parse_errors)
        if ast is None:
            continue
        headers = [node for node in walk(ast.get("blocks", [])) if node.get("t") == "Header"]
        heading_ids = {node["c"][1][0] for node in headers if node.get("c")}
        metadata[rel] = {"ast": ast, "ids": explicit_ids | heading_ids}
        if manuscript:
            detected = sum(1 for _, line in visible_lines(source) if ATX_HEADING.match(line))
            if detected != len(headers):
                errors.append(report(rel, "use only ATX-style headings (#); renderer found a different heading count"))
        # Verify every source can be compiled into semantic HTML/MathML.
        render = subprocess.run(
            [pandoc, "--from", PANDOC_READER, "--to", "html5", "--standalone", "--mathml", "-o", "/dev/null", str(path)],
            capture_output=True, text=True, check=False,
        )
        if render.returncode:
            errors.append(report(rel, "HTML/MathML render failed: " + render.stderr.strip()))

    for rel, info in metadata.items():
        for node in walk(info["ast"].get("blocks", [])):
            kind = node.get("t")
            if kind not in ("Link", "Image"):
                continue
            content = node.get("c", [])
            if len(content) < 3:
                continue
            if kind == "Image" and not inline_text(content[1]).strip():
                errors.append(report(rel, "image is missing alt text"))
            target = content[2][0]
            url = urlsplit(target)
            if url.scheme or url.netloc or url.path.startswith("/"):
                continue  # External or site-root link; offline check cannot confirm it.
            if not url.path and not url.fragment:
                continue
            file_path = unquote(url.path)
            destination = (root / rel.parent / file_path).resolve() if file_path else (root / rel).resolve()
            try:
                dest_rel = destination.relative_to(root)
            except ValueError:
                errors.append(report(rel, f"link escapes repository: {target}"))
                continue
            if not destination.exists():
                errors.append(report(rel, f"broken local link: {target}"))
                continue
            if url.fragment and dest_rel in metadata:
                fragment = unquote(url.fragment)
                if fragment not in metadata[dest_rel]["ids"]:
                    errors.append(report(rel, f"unresolved Markdown section link: {target}"))
    return errors


def git_markdown_paths(root: Path) -> list[Path]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True)
    return sorted(Path(p.decode("utf-8")) for p in result.stdout.split(b"\0") if p and Path(p.decode("utf-8")).suffix.lower() in SOURCE_EXTENSIONS)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    paths = git_markdown_paths(root)
    if not paths:
        print("ERROR: No tracked Markdown sources found.", file=sys.stderr)
        return 1
    errors = validate_repository(root, paths)
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        print(f"Source validation FAILED: {len(errors)} problem(s) in {len(paths)} Markdown files.", file=sys.stderr)
        return 1
    print(f"Source validation passed: {len(paths)} tracked Markdown files checked (UTF-8/NFC, structure, local links, GFM, HTML/MathML).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
