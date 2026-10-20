"""Bounded binary metadata differences, without validating or modifying firmware.

Inputs are read only. Paths and byte previews are omitted unless requested.
Reports never establish checksum correctness, patch safety or target identity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Iterable
import zlib

DEFAULT_MAX_BYTES = 16 * 1024 * 1024
MAX_BYTES = 256 * 1024 * 1024
DEFAULT_MAX_RANGES = 1024


def _bounded_integer(value: int, label: str, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{label} must be an integer from 1 to {maximum}")
    return value


def _boolean(value: bool, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be a boolean")
    return value


def _read_bounded(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError(f"input must be an existing regular file: {path}")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"input exceeds --max-input-bytes ({limit}): {path}")
    return data


def _range(start: int, end: int, original: bytes, modified: bytes,
           include_previews: bool) -> dict:
    row = {"start": start, "end_exclusive": end, "length": end - start,
           "start_hex": f"0x{start:X}", "end_exclusive_hex": f"0x{end:X}"}
    if include_previews:
        row["original_preview"] = original[start:min(end, start + 32)].hex(" ").upper()
        row["modified_preview"] = modified[start:min(end, start + 32)].hex(" ").upper()
    return row


def changed_ranges(original: bytes, modified: bytes, *, max_ranges: int = DEFAULT_MAX_RANGES,
                   include_previews: bool = False) -> dict:
    """Return bounded consecutive diff ranges and exact totals, including length changes."""
    _bounded_integer(max_ranges, "max_ranges", 100000)
    _boolean(include_previews, "include_previews")
    if not isinstance(original, bytes) or not isinstance(modified, bytes):
        raise TypeError("original and modified must be bytes")
    ranges = []
    count = changed_bytes = 0
    start = None
    common = min(len(original), len(modified))
    end = max(len(original), len(modified))
    for index in range(end + 1):
        differs = index < end and (index >= common or original[index] != modified[index])
        if differs and start is None:
            start = index
        elif not differs and start is not None:
            count += 1
            changed_bytes += index - start
            if len(ranges) < max_ranges:
                ranges.append(_range(start, index, original, modified, include_previews))
            start = None
    return {"changed_ranges": ranges, "changed_range_count": count,
            "reported_range_count": len(ranges), "ranges_truncated": count > len(ranges),
            "changed_byte_span_total": changed_bytes}


def build_report(original_path: Path, modified_path: Path,
                 expected_original_sha256: str | None = None, *,
                 max_input_bytes: int = DEFAULT_MAX_BYTES, max_ranges: int = DEFAULT_MAX_RANGES,
                 include_paths: bool = False, include_previews: bool = False,
                 fail_on_size_mismatch: bool = False) -> dict:
    """Build metadata after validating limits and an optional exact source hash.

    A matching hash is an identity observation, never ECU/OS compatibility proof.
    No files are written by this API.
    """
    _bounded_integer(max_input_bytes, "max_input_bytes", MAX_BYTES)
    _bounded_integer(max_ranges, "max_ranges", 100000)
    _boolean(include_paths, "include_paths")
    _boolean(include_previews, "include_previews")
    _boolean(fail_on_size_mismatch, "fail_on_size_mismatch")
    if expected_original_sha256 is not None:
        if not isinstance(expected_original_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_original_sha256):
            raise ValueError("expected original SHA256 must contain exactly 64 hexadecimal characters")
        expected_original_sha256 = expected_original_sha256.upper()
    original_path, modified_path = Path(original_path), Path(modified_path)
    original = _read_bounded(original_path, max_input_bytes)
    modified = _read_bounded(modified_path, max_input_bytes)

    def identity(data: bytes, path: Path) -> dict:
        item = {"size": len(data), "sha256": hashlib.sha256(data).hexdigest().upper(),
                "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08X}"}
        if include_paths:
            item["path"] = str(path)
        return item

    source, result = identity(original, original_path), identity(modified, modified_path)
    if expected_original_sha256 and source["sha256"] != expected_original_sha256:
        raise ValueError("original SHA256 does not match expected hash; no report was written")
    if fail_on_size_mismatch and len(original) != len(modified):
        raise ValueError("binary sizes differ; no report was written")
    source["expected_sha256"] = expected_original_sha256
    source["expected_sha256_match"] = True if expected_original_sha256 else None
    return {"status": "metadata_only_not_flash_ready", "checksum_status": "not_calculated",
            "original": source, "modified": result, "same_size": len(original) == len(modified),
            **changed_ranges(original, modified, max_ranges=max_ranges, include_previews=include_previews),
            "notes": ["CRC32 is file metadata, not a validated PCM checksum.",
                      "No target, code flow, patch safety or hardware qualification is established."]}


def _markdown(report: dict) -> str:
    lines = ["# Binary difference metadata", "", f"Status: `{report['status']}`", "",
             f"Checksum status: `{report['checksum_status']}`", "",
             "| Input | Size | SHA256 | CRC32 |", "|---|---:|---|---|"]
    for role in ("original", "modified"):
        item = report[role]
        lines.append(f"| {role} | {item['size']} | `{item['sha256']}` | `{item['crc32']}` |")
    lines += ["", f"Changed bytes: {report['changed_byte_span_total']}",
              f"Changed ranges: {report['changed_range_count']}",
              f"Ranges truncated: {str(report['ranges_truncated']).lower()}", "",
              "| Start | End exclusive | Length |", "|---|---|---:|"]
    for row in report["changed_ranges"]:
        lines.append(f"| `{row['start_hex']}` | `{row['end_exclusive_hex']}` | {row['length']} |")
    paths = [(role, report[role]["path"]) for role in ("original", "modified")
             if "path" in report[role]]
    if paths:
        # Keep optional details outside tables and escape user-controlled paths.
        import html
        lines += ["", "## Input paths", ""]
        lines += [f"- {role}: <code>{html.escape(json.dumps(path))}</code>" for role, path in paths]
    previews = [row for row in report["changed_ranges"] if "original_preview" in row]
    if previews:
        lines += ["", "## Byte previews", "",
                  "| Start | Original preview | Modified preview |", "|---|---|---|"]
        for row in previews:
            lines.append(f"| `{row['start_hex']}` | `{row['original_preview']}` | `{row['modified_preview']}` |")
    lines += ["", *report["notes"]]
    return "\n".join(lines) + "\n"


def _write_reports(outputs: list[tuple[Path, str]], inputs: Iterable[Path]) -> None:
    """Reserve all explicit reports exclusively; roll back only newly created files on failure."""
    resolved_inputs = {Path(path).resolve() for path in inputs}
    resolved_outputs = []
    for path, _ in outputs:
        resolved = path.resolve()
        if resolved in resolved_inputs:
            raise ValueError("report output aliases an input")
        if resolved in resolved_outputs:
            raise ValueError("report outputs alias each other")
        if path.exists() or path.is_symlink():
            # Refuse any existing path, covering hard links as well as symlinks.
            raise FileExistsError(f"report output already exists: {path}")
        if not path.parent.is_dir():
            raise ValueError(f"report parent directory does not exist: {path.parent}")
        resolved_outputs.append(resolved)
    created = []
    failure = None
    try:
        for path, content in outputs:
            stream = path.open("x", encoding="utf-8", newline="\n")
            identity = os.fstat(stream.fileno())
            created.append((path, stream, (identity.st_dev, identity.st_ino)))
        for (_, content), (_, stream, _) in zip(outputs, created):
            stream.write(content)
            stream.flush()
    except BaseException as exc:
        failure = exc
    finally:
        # A flush/close failure must not prevent closing the other reservations.
        # Treat a close failure after successful writes as a failed publication.
        for _, stream, _ in created:
            try:
                stream.close()
            except (OSError, ValueError) as exc:
                if failure is None:
                    failure = exc
        if failure is not None:
            cleanup_failed = []
            for path, _, identity in created:
                try:
                    current = path.lstat()
                    # Never delete a user file/symlink that replaced our reservation.
                    if (current.st_dev, current.st_ino) == identity:
                        path.unlink()
                except FileNotFoundError:
                    pass
                except OSError:
                    cleanup_failed.append(str(path))
            if cleanup_failed:
                raise OSError(f"{failure}; could not remove new report output(s): {', '.join(cleanup_failed)}") from failure
    if failure is not None:
        raise failure


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("modified", type=Path)
    parser.add_argument("--expected-original-sha256")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--fail-on-size-mismatch", action="store_true")
    parser.add_argument("--max-input-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--max-ranges", type=int, default=DEFAULT_MAX_RANGES)
    parser.add_argument("--include-paths", action="store_true", help="include input paths in reports")
    parser.add_argument("--include-byte-previews", action="store_true", help="include up to 32 bytes per reported range")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.original, args.modified, args.expected_original_sha256,
                              max_input_bytes=args.max_input_bytes, max_ranges=args.max_ranges,
                              include_paths=args.include_paths, include_previews=args.include_byte_previews,
                              fail_on_size_mismatch=args.fail_on_size_mismatch)
        outputs = []
        if args.json_out:
            outputs.append((args.json_out, json.dumps(report, indent=2, sort_keys=True) + "\n"))
        if args.markdown_out:
            outputs.append((args.markdown_out, _markdown(report)))
        _write_reports(outputs, (args.original, args.modified))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if outputs:
        print(f"Changed bytes: {report['changed_byte_span_total']}; ranges: {report['changed_range_count']}; checksum: not_calculated")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
