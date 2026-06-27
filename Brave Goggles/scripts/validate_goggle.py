#!/usr/bin/env python3
"""Lightweight local checks for Brave Search Goggle files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_METADATA = {"name", "description", "public", "author"}
OPTIONAL_METADATA = {"homepage", "issues", "transferred_to", "avatar", "license"}
KNOWN_METADATA = REQUIRED_METADATA | OPTIONAL_METADATA
TARGET_OPTIONS = {"inurl", "intitle", "indescription", "incontent"}
ACTION_RE = re.compile(r"^(boost|downrank)(?:=(\d+))?$|^discard$")
METADATA_RE = re.compile(r"^!\s*([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
DOMAIN_RE = re.compile(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Brave Search .goggle file.")
    parser.add_argument("path", type=Path, help="Path to a .goggle file")
    return parser.parse_args()


def add(messages: list[str], line_no: int | None, message: str) -> None:
    prefix = f"line {line_no}: " if line_no is not None else ""
    messages.append(prefix + message)


def validate_metadata(metadata: dict[str, str], errors: list[str], warnings: list[str]) -> None:
    missing = sorted(REQUIRED_METADATA - metadata.keys())
    for key in missing:
        add(errors, None, f"missing required metadata: ! {key}: ...")

    for key, value in sorted(metadata.items()):
        if key not in KNOWN_METADATA:
            add(warnings, None, f"unknown metadata key: {key}")
        if not value.strip():
            add(errors, None, f"metadata value for {key} is empty")

    public = metadata.get("public")
    if public is not None and public.strip().lower() not in {"true", "false"}:
        add(errors, None, "metadata public must be true or false")

    avatar = metadata.get("avatar")
    if avatar is not None and not HEX_COLOR_RE.match(avatar.strip()):
        add(errors, None, "metadata avatar must be a 6-digit hex color such as #2F6FED")


def validate_option(option: str, line_no: int, errors: list[str], warnings: list[str]) -> str | None:
    if not option:
        add(errors, line_no, "empty option after comma")
        return None

    action_match = ACTION_RE.match(option)
    if action_match:
        action_name = "discard" if option == "discard" else action_match.group(1)
        strength = action_match.group(2)
        if strength is not None:
            value = int(strength)
            if value < 1 or value > 10:
                add(errors, line_no, f"{action_name} strength must be between 1 and 10")
        return action_name

    if option.startswith("site="):
        domain = option.split("=", 1)[1].strip()
        if not domain:
            add(errors, line_no, "site option needs a domain")
        elif "*" in domain or "/" in domain or ":" in domain:
            add(errors, line_no, "site option should be a bare domain, for example site=example.com")
        elif not DOMAIN_RE.match(domain):
            add(warnings, line_no, f"site value looks unusual: {domain}")
        return None

    if option in TARGET_OPTIONS:
        add(warnings, line_no, f"{option} is documented as future-facing; Brave may not support it yet")
        return None

    add(warnings, line_no, f"unknown option: {option}")
    return None


def validate_instruction(line: str, line_no: int, errors: list[str], warnings: list[str]) -> str:
    if len(line) > 500:
        add(errors, line_no, "instruction is longer than 500 characters")
    if line.count("*") > 2:
        add(errors, line_no, "instruction uses more than 2 wildcard characters")
    if line.count("^") > 2:
        add(errors, line_no, "instruction uses more than 2 caret characters")

    action = "boost"
    pattern, sep, option_text = line.partition("$")

    if not sep:
        return action

    options = [part.strip() for part in option_text.split(",")]
    seen_actions: list[str] = []
    for option in options:
        parsed_action = validate_option(option, line_no, errors, warnings)
        if parsed_action:
            seen_actions.append(parsed_action)

    if len(seen_actions) > 1:
        add(errors, line_no, f"multiple actions in one instruction: {', '.join(seen_actions)}")
    elif seen_actions:
        action = seen_actions[0]

    if not pattern.strip() and action == "discard" and "site=" not in option_text:
        add(warnings, line_no, "generic $discard creates an allowlist and removes unmatched results")

    return action


def validate(path: Path) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    metadata: dict[str, str] = {}
    action_counts = {"boost": 0, "downrank": 0, "discard": 0}
    instruction_count = 0

    if not path.exists():
        add(errors, None, f"file does not exist: {path}")
        print_report(path, metadata, instruction_count, action_counts, errors, warnings)
        return 1

    size = path.stat().st_size
    if size > 2 * 1024 * 1024:
        add(errors, None, "file is larger than Brave's 2 MB limit")

    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        metadata_match = METADATA_RE.match(line)
        if metadata_match:
            key, value = metadata_match.groups()
            normalized_key = key.lower()
            if normalized_key in KNOWN_METADATA:
                metadata[normalized_key] = value.strip()
                continue

        if line.startswith("!"):
            continue

        instruction_count += 1
        action = validate_instruction(line, line_no, errors, warnings)
        action_counts[action] += 1

    if instruction_count > 100_000:
        add(errors, None, "file has more than 100,000 active instructions")
    if instruction_count == 0:
        add(warnings, None, "no active instructions yet; uncomment or add rules before submitting")

    validate_metadata(metadata, errors, warnings)
    print_report(path, metadata, instruction_count, action_counts, errors, warnings)
    return 1 if errors else 0


def print_report(
    path: Path,
    metadata: dict[str, str],
    instruction_count: int,
    action_counts: dict[str, int],
    errors: list[str],
    warnings: list[str],
) -> None:
    print(f"Goggle: {path}")
    print(f"Metadata: {', '.join(sorted(metadata)) if metadata else 'none'}")
    print(f"Active instructions: {instruction_count}")
    print(
        "Actions: "
        f"boost={action_counts['boost']}, "
        f"downrank={action_counts['downrank']}, "
        f"discard={action_counts['discard']}"
    )

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"- {error}")
        return

    print("\nOK: no blocking issues found.")


def main() -> int:
    args = parse_args()
    return validate(args.path)


if __name__ == "__main__":
    sys.exit(main())
