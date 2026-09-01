#!/usr/bin/env python3
"""Static validation helpers for the LazyBlog editorial campaign.

This deliberately checks only facts available in the local repositories. Live
WordPress state, source quality, link safety, and factual accuracy still need
their own evidence before a post can enter the verified ledger.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FRONT_MATTER = re.compile(r"\A---\n(?P<header>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)
LEDGER_TOTAL = re.compile(r"As of the verified commit, \*\*(\d+) posts\*\*")
LEDGER_MAIN_LIST = re.compile(
    r"As of the verified commit.*?\n\n`([^`]+)`", re.DOTALL
)
CATEGORY_LIST = re.compile(r"^Posts: `([^`]+)`\.$", re.MULTILINE)
SCALAR = re.compile(r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*):\s*(?P<value>.*?)\s*$")
HEADING = re.compile(r"^(#{1,6})\s+\S")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})([^`]*)$")
ORDERED_ITEM = re.compile(r"^(\s*)\d+[.)]\s+\S")
UNORDERED_ITEM = re.compile(r"^(\s*)[-+*]\s+\S")
TASK_ITEM = re.compile(r"^(\s*)[-+*]\s+\[[ xX]\]\s+\S")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
BLOCKQUOTE = re.compile(r"^(\s*(?:>\s*)+)\S")
MARKDOWN_URL = re.compile(r"(?:\]\(|<)(https?://[^)>\s]+)")


class EditorialValidationError(ValueError):
    """Raised when static editorial evidence is internally inconsistent."""


@dataclass(frozen=True)
class MarkdownDocument:
    path: Path
    metadata: dict[str, str]
    body: str


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def read_document(path: Path) -> MarkdownDocument:
    text = path.read_text(encoding="utf-8")
    match = FRONT_MATTER.match(text)
    if not match:
        raise EditorialValidationError(f"{path}: missing or malformed front matter")
    metadata: dict[str, str] = {}
    for line in match.group("header").splitlines():
        scalar = SCALAR.match(line)
        if scalar:
            metadata[scalar.group("key")] = _unquote(scalar.group("value"))
    return MarkdownDocument(path=path, metadata=metadata, body=match.group("body"))


def _parse_ids(value: str, label: str) -> list[int]:
    try:
        ids = [int(item) for item in re.split(r",\s*", value.strip()) if item]
    except ValueError as exc:
        raise EditorialValidationError(f"{label}: non-numeric post ID") from exc
    if ids != sorted(ids):
        raise EditorialValidationError(f"{label}: post IDs are not sorted")
    if len(ids) != len(set(ids)):
        raise EditorialValidationError(f"{label}: duplicate post ID")
    return ids


def validate_ledger(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    declared = LEDGER_TOTAL.search(text)
    main_list = LEDGER_MAIN_LIST.search(text)
    if not declared or not main_list:
        raise EditorialValidationError(f"{path}: cannot find verified count and post list")
    ids = _parse_ids(main_list.group(1), "verified list")
    total = int(declared.group(1))
    if len(ids) != total:
        raise EditorialValidationError(
            f"{path}: declares {total} verified posts but lists {len(ids)}"
        )
    categories = list(CATEGORY_LIST.finditer(text))
    for index, match in enumerate(categories, start=1):
        category_ids = _parse_ids(match.group(1), f"category {index}")
        missing = sorted(set(category_ids) - set(ids))
        if missing:
            raise EditorialValidationError(
                f"category {index}: IDs not present in verified list: {missing}"
            )
    return {"verified_posts": total, "categories": len(categories)}


def _required(metadata: dict[str, str], key: str, path: Path) -> str:
    value = metadata.get(key, "").strip()
    if not value:
        raise EditorialValidationError(f"{path}: missing {key!r} front-matter value")
    return value


def _structural_signature(
    body: str, path: Path
) -> tuple[tuple[int, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    headings: list[int] = []
    fences: list[str] = []
    blocks: list[str] = []
    urls: list[str] = []
    active_fence: tuple[str, int] | None = None
    for line in body.splitlines():
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)
            if active_fence is None:
                active_fence = (marker[0], len(marker))
                fences.append(fence.group(2).strip())
            elif marker[0] == active_fence[0] and len(marker) >= active_fence[1]:
                active_fence = None
            continue
        if active_fence is None:
            heading = HEADING.match(line)
            if heading:
                headings.append(len(heading.group(1)))
                blocks.append(f"h{len(heading.group(1))}")
            elif task := TASK_ITEM.match(line):
                blocks.append(f"task:{len(task.group(1))}")
            elif ordered := ORDERED_ITEM.match(line):
                blocks.append(f"ol:{len(ordered.group(1))}")
            elif unordered := UNORDERED_ITEM.match(line):
                blocks.append(f"ul:{len(unordered.group(1))}")
            elif TABLE_ROW.match(line):
                blocks.append("table")
            elif quote := BLOCKQUOTE.match(line):
                blocks.append(f"quote:{quote.group(1).count('>')}")
            urls.extend(MARKDOWN_URL.findall(line))
    if active_fence is not None:
        raise EditorialValidationError(f"{path}: unbalanced fenced code block")
    if 1 in headings:
        raise EditorialValidationError(f"{path}: body H1 found outside a fenced archive")
    return tuple(headings), tuple(fences), tuple(blocks), tuple(urls)


def _check_trailing_whitespace(document: MarkdownDocument) -> None:
    lines = document.path.read_text(encoding="utf-8").splitlines()
    bad = [index for index, line in enumerate(lines, start=1) if line.rstrip() != line]
    if bad:
        raise EditorialValidationError(
            f"{document.path}: trailing whitespace on lines {bad[:8]}"
        )


def expected_translation_languages(source_language: str) -> tuple[str, str]:
    choices = {
        "en": ("ja", "zh"),
        "ja": ("en", "zh"),
        "zh": ("en", "ja"),
    }
    try:
        return choices[source_language]
    except KeyError as exc:
        raise EditorialValidationError(
            f"unsupported source language {source_language!r}"
        ) from exc


def validate_post(blog_root: Path, post_id: int) -> dict[str, object]:
    post_dir = blog_root / "content" / "posts" / str(post_id)
    source = read_document(post_dir / "post.md")
    source_language = _required(source.metadata, "source_language", source.path)
    languages = expected_translation_languages(source_language)
    documents = [source]
    for language in languages:
        path = post_dir / "translations" / f"{language}.md"
        translation = read_document(path)
        actual_language = _required(translation.metadata, "language", path)
        if actual_language != language:
            raise EditorialValidationError(
                f"{path}: declares language {actual_language!r}, expected {language!r}"
            )
        documents.append(translation)

    identity_keys = ("id", "slug", "date", "status", "link", "source_language")
    baseline = tuple(_required(source.metadata, key, source.path) for key in identity_keys)
    if baseline[0] != str(post_id):
        raise EditorialValidationError(
            f"{source.path}: declares ID {baseline[0]!r}, expected {post_id}"
        )
    source_signature = _structural_signature(source.body, source.path)
    for document in documents:
        _required(document.metadata, "title", document.path)
        _check_trailing_whitespace(document)
        identity = tuple(
            _required(document.metadata, key, document.path) for key in identity_keys
        )
        if identity != baseline:
            raise EditorialValidationError(
                f"{document.path}: identity front matter differs from source"
            )
        signature = _structural_signature(document.body, document.path)
        if signature != source_signature:
            raise EditorialValidationError(
                f"{document.path}: Markdown blocks, fence languages, or links differ from source"
            )

    manifest_path = post_dir / "lazyblog.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("post_id") != post_id:
        raise EditorialValidationError(
            f"{manifest_path}: post_id differs from requested post"
        )
    return {
        "post_id": post_id,
        "source_language": source_language,
        "translations": list(languages),
        "headings": len(source_signature[0]),
        "fences": len(source_signature[1]),
        "blocks": len(source_signature[2]),
        "links": len(source_signature[3]),
        "files": 4,
    }


def _print_result(result: dict[str, object]) -> None:
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    ledger = commands.add_parser("ledger", help="validate the public editorial ledger")
    ledger.add_argument("path", type=Path)
    post = commands.add_parser("post", help="validate one local four-file post bundle")
    post.add_argument("blog_root", type=Path)
    post.add_argument("post_id", type=int)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "ledger":
            result = validate_ledger(args.path)
        else:
            result = validate_post(args.blog_root, args.post_id)
    except (EditorialValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
