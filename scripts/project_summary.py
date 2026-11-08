#!/usr/bin/env python3
"""Compact structural summary of a codebase. Stdlib only. Python 3.9+."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

SKIP_DIR_NAMES = frozenset(
    {
        ".dart_tool",
        ".git",
        ".hg",
        ".idea",
        ".mypy_cache",
        ".next",
        ".nuxt",
        ".output",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".turbo",
        ".venv",
        ".vscode",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "out",
        "Pods",
        "target",
        "vendor",
        "venv",
    }
)

SKIP_LINE_NAMES = frozenset(
    {
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lock",
        "bun.lockb",
        "pubspec.lock",
        "poetry.lock",
        "Cargo.lock",
        "composer.lock",
        "Gemfile.lock",
    }
)

SKIP_LINE_SUFFIXES = (".min.js", ".min.css", ".map", ".lock")

BINARY_SUFFIXES = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".icns",
        ".pdf",
        ".zip",
        ".gz",
        ".tar",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
        ".mp3",
        ".mp4",
        ".mov",
        ".wasm",
        ".so",
        ".dylib",
        ".dll",
        ".exe",
        ".bin",
        ".class",
        ".jar",
        ".pyc",
        ".pyo",
        ".o",
        ".a",
        ".sqlite",
        ".db",
    }
)

SOURCE_SUFFIXES = frozenset(
    {
        ".dart",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".py",
        ".pyi",
        ".rs",
        ".go",
        ".java",
        ".kt",
        ".swift",
        ".rb",
        ".php",
        ".cs",
        ".c",
        ".cc",
        ".cpp",
        ".h",
        ".hpp",
        ".md",
        ".mdx",
        ".json",
        ".yml",
        ".yaml",
        ".toml",
        ".css",
        ".scss",
        ".html",
        ".sql",
        ".sh",
        ".graphql",
        ".vue",
        ".svelte",
    }
)

KEY_CANDIDATES = (
    "README.md",
    "readme.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "pubspec.yaml",
    "analysis_options.yaml",
    "l10n.yaml",
    "lib/main.dart",
    "lib/app.dart",
    "package.json",
    "next.config.ts",
    "next.config.js",
    "next.config.mjs",
    "next.config.cjs",
    "tsconfig.json",
    "jsconfig.json",
    "middleware.ts",
    "middleware.js",
    "app/layout.tsx",
    "app/layout.ts",
    "app/layout.jsx",
    "app/page.tsx",
    "app/page.ts",
    "app/page.jsx",
    "pages/_app.tsx",
    "pages/_app.js",
    "pages/index.tsx",
    "pages/index.js",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "requirements-dev.txt",
    "Pipfile",
    "poetry.lock",
    "pytest.ini",
    "tox.ini",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    ".python-version",
)

CI_GLOBS = (
    ".github/workflows",
    ".gitlab-ci.yml",
    ".circleci/config.yml",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
)

MARKER_KEYS = (b"TODO", b"FIXME", b"HACK", b"XXX")
MAX_SCAN_BYTES = 2_000_000
MAX_HOTSPOTS = 8
MAX_EXT = 20
MAX_KEY_FILES = 24
MAX_SUGGESTED = 12


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or (name.startswith(".") and name not in {".github", ".gitlab"})


def is_binary_path(path: Path) -> bool:
    return path.suffix.lower() in BINARY_SUFFIXES


def skip_line_count(path: Path) -> bool:
    name = path.name
    if name in SKIP_LINE_NAMES:
        return True
    lower = name.lower()
    return any(lower.endswith(suf) for suf in SKIP_LINE_SUFFIXES)


def read_text_head(path: Path, limit: int = 8000) -> str:
    try:
        data = path.read_bytes()[:limit]
    except OSError:
        return ""
    return data.decode("utf-8", errors="ignore")


def load_package_json(root: Path) -> dict:
    path = root / "package.json"
    if not path.is_file():
        return {}
    try:
        payload = json.loads(read_text_head(path, 120_000) or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def deps_of(package: dict) -> dict:
    merged: dict = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package.get(key)
        if isinstance(value, dict):
            merged.update(value)
    return merged


def has_next_config(root: Path) -> bool:
    return any(
        (root / name).is_file()
        for name in (
            "next.config.ts",
            "next.config.js",
            "next.config.mjs",
            "next.config.cjs",
        )
    )


def detect_types(root: Path, ext_counts: Counter[str], files: list[str]) -> tuple[str, list[str], dict[str, list[str]]]:
    files_set = set(files)
    package = load_package_json(root)
    deps = deps_of(package)
    pubspec = root / "pubspec.yaml"
    pubspec_text = read_text_head(pubspec) if pubspec.is_file() else ""

    dart_files = ext_counts.get(".dart", 0)
    py_files = ext_counts.get(".py", 0) + ext_counts.get(".pyi", 0)
    ts_files = ext_counts.get(".ts", 0) + ext_counts.get(".tsx", 0)

    signals: dict[str, list[str]] = {}
    scores: dict[str, int] = {}

    flutter_hits: list[str] = []
    if pubspec.is_file():
        flutter_hits.append("pubspec.yaml")
        if "flutter:" in pubspec_text:
            flutter_hits.append("pubspec.yaml:flutter")
    if (root / "lib").is_dir() and dart_files:
        flutter_hits.append("lib/")
    if "lib/main.dart" in files_set:
        flutter_hits.append("lib/main.dart")
    if dart_files:
        flutter_hits.append(f"{dart_files}_dart_files")
    if flutter_hits:
        signals["flutter"] = flutter_hits
        scores["flutter"] = dart_files * 4 + (25 if "pubspec.yaml:flutter" in flutter_hits else 0) + (
            10 if pubspec.is_file() else 0
        )

    next_hits: list[str] = []
    if "next" in deps:
        next_hits.append("package.json:next")
    if has_next_config(root):
        next_hits.append("next.config")
    for marker in (
        "app/layout.tsx",
        "app/layout.ts",
        "app/layout.jsx",
        "app/page.tsx",
        "app/page.ts",
        "pages/_app.tsx",
        "pages/_app.js",
        "pages/index.tsx",
    ):
        if marker in files_set:
            next_hits.append(marker)
    if (root / "app").is_dir() and "next" in deps:
        next_hits.append("app/")
    if (root / "pages").is_dir() and "next" in deps:
        next_hits.append("pages/")
    if next_hits:
        signals["nextjs"] = next_hits
        scores["nextjs"] = ts_files + (40 if "next" in deps else 0) + (15 if has_next_config(root) else 0)

    py_hits: list[str] = []
    for marker in ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile"):
        if (root / marker).is_file():
            py_hits.append(marker)
    if py_files:
        py_hits.append(f"{py_files}_py_files")
    if py_hits and (py_files >= 3 or any(h in py_hits for h in ("pyproject.toml", "setup.py", "requirements.txt", "Pipfile"))):
        signals["python"] = py_hits
        scores["python"] = py_files * 3 + (8 * (len(py_hits) - (1 if py_files else 0)))

    ranked = [name for name, score in sorted(scores.items(), key=lambda item: (-item[1], item[0])) if score > 0]
    if not ranked:
        return "generic", ["generic"], {"generic": ["no_stack_manifest"]}
    return ranked[0], ranked, signals


def existing_key_files(root: Path) -> list[str]:
    found: list[str] = []
    for candidate in KEY_CANDIDATES:
        path = root / candidate
        if path.is_file():
            found.append(candidate)
        if len(found) >= MAX_KEY_FILES:
            break
    return found


def find_ci(root: Path) -> list[str]:
    hits: list[str] = []
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        for path in sorted(workflows.iterdir()):
            if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}:
                hits.append(rel(root, path))
            if len(hits) >= 8:
                return hits
    for candidate in CI_GLOBS[1:]:
        path = root / candidate
        if path.is_file():
            hits.append(candidate)
    return hits


def walk(root: Path) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    skipped: set[str] = set()
    for dirpath, dirnames, filenames in os_walk(root):
        kept: list[str] = []
        for name in dirnames:
            if should_skip_dir(name):
                skipped.add(name)
            else:
                kept.append(name)
        dirnames[:] = kept
        current = Path(dirpath)
        for name in filenames:
            files.append(current / name)
    return files, sorted(skipped)


def os_walk(root: Path):
    # Local wrapper so tests can reason about skip behavior without importing os at call sites.
    import os

    return os.walk(root, followlinks=False)


def scan_source(path: Path) -> tuple[int, Counter[str]]:
    markers: Counter[str] = Counter()
    try:
        size = path.stat().st_size
    except OSError:
        return 0, markers
    if size == 0:
        return 0, markers
    if size > MAX_SCAN_BYTES:
        return max(1, size // 80), markers
    try:
        data = path.read_bytes()
    except OSError:
        return 0, markers
    lines = data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1)
    upper = data.upper()
    for key in MARKER_KEYS:
        count = upper.count(key)
        if count:
            markers[key.decode("ascii")] = count
    return lines, markers


def summarize(root: Path) -> dict:
    all_files, skipped_dirs = walk(root)
    ext_counts: Counter[str] = Counter()
    line_counts: Counter[str] = Counter()
    total_lines = 0
    source_files = 0
    test_files = 0
    hotspots: list[tuple[int, str]] = []
    markers: Counter[str] = Counter()
    relative_files: list[str] = []

    for path in all_files:
        suffix = path.suffix.lower() or path.name
        ext_counts[suffix] += 1
        relative = rel(root, path)
        relative_files.append(relative)

        lowered = relative.lower()
        if "test" in lowered or lowered.endswith("_test.dart"):
            if suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".dart"}:
                test_files += 1

        if is_binary_path(path) or skip_line_count(path):
            continue
        if suffix not in SOURCE_SUFFIXES and not path.name.startswith("Dockerfile"):
            continue

        lines, file_markers = scan_source(path)
        if lines <= 0:
            continue
        source_files += 1
        total_lines += lines
        line_counts[suffix] += lines
        markers.update(file_markers)
        if suffix in {".dart", ".ts", ".tsx", ".js", ".jsx", ".py"} and lines >= 250:
            hotspots.append((lines, relative))

    hotspots.sort(reverse=True)
    hotspot_payload = [{"path": path, "lines": lines} for lines, path in hotspots[:MAX_HOTSPOTS]]

    primary, types, signals = detect_types(root, ext_counts, relative_files)
    key_files = existing_key_files(root)
    suggested = list(dict.fromkeys([*key_files[:8], *[item["path"] for item in hotspot_payload]]))
    suggested = suggested[:MAX_SUGGESTED]

    top_ext = ext_counts.most_common(MAX_EXT)
    by_extension = {name: count for name, count in top_ext}
    other_files = sum(ext_counts.values()) - sum(by_extension.values())
    if other_files:
        by_extension["__other__"] = other_files

    top_lines = line_counts.most_common(MAX_EXT)
    lines_by_ext = {name: count for name, count in top_lines}

    file_count = len(all_files)
    reason = (
        f"~{total_lines} linhas-fonte em {source_files} arquivos "
        f"({file_count} arquivos contados; pastas ignoradas: "
        f"{', '.join(skipped_dirs) or 'nenhuma'}). "
        "Não ler o repositório inteiro; usar key_files e hotspots."
    )

    return {
        "root": str(root),
        "project_type": primary,
        "project_types": types,
        "signals": signals,
        "files": {
            "counted": file_count,
            "source": source_files,
            "tests": test_files,
            "skipped_dirs": skipped_dirs,
            "by_extension": by_extension,
        },
        "lines": {
            "approx_source": total_lines,
            "by_extension": lines_by_ext,
        },
        "key_files": key_files,
        "ci": find_ci(root),
        "hotspots": hotspot_payload,
        "markers": dict(markers),
        "read_guidance": {
            "do_not_read_all": True,
            "reason": reason,
            "max_files_to_read": min(12, max(6, 4 + len(hotspot_payload))),
            "suggested_reads": suggested,
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit a compact JSON structural summary. Does not dump file contents."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Project root (default: current directory)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Indent JSON (larger). Default is compact.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        eprint(f"project_summary: path does not exist: {root}")
        return 2
    if not root.is_dir():
        eprint(f"project_summary: not a directory: {root}")
        return 2

    payload = summarize(root)
    if args.pretty:
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        json.dump(payload, sys.stdout, ensure_ascii=False, separators=(",", ":"))
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
