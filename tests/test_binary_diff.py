"""Redistributable synthetic vectors; no firmware fixtures or hardware access."""

import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from holden_wip.binary_diff import _markdown, _write_reports, build_report, changed_ranges, main


class BinaryDiffTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="binary diff tests ")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.original = self.root / "original data.bin"
        self.modified = self.root / "modified data.bin"
        self.original.write_bytes(b"\x00\x01\x02\x03")
        self.modified.write_bytes(b"\x00\xFF\x02\x04")

    def cli(self, *args):
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            result = main([str(self.original), str(self.modified), *map(str, args)])
        return result, out.getvalue(), err.getvalue()

    def test_exact_synthetic_ranges_and_privacy_defaults(self):
        report = build_report(self.original, self.modified)
        self.assertEqual(report["changed_range_count"], 2)
        self.assertEqual(report["changed_byte_span_total"], 2)
        self.assertEqual([(r["start"], r["end_exclusive"]) for r in report["changed_ranges"]], [(1, 2), (3, 4)])
        self.assertNotIn("path", report["original"])
        self.assertNotIn("original_preview", report["changed_ranges"][0])
        self.assertEqual(report["checksum_status"], "not_calculated")

    def test_addition_deletion_and_adjacent_changed_tail(self):
        for before, after in ((b"abc", b"abXYZ"), (b"abXYZ", b"abc")):
            report = changed_ranges(before, after)
            self.assertEqual(report["changed_range_count"], 1)
            self.assertEqual(report["changed_byte_span_total"], 3)
            self.assertEqual(report["changed_ranges"][0]["start"], 2)
        self.assertEqual(changed_ranges(b"", b"")["changed_range_count"], 0)

    def test_range_limit_retains_exact_totals(self):
        report = changed_ranges(bytes(100), bytes([1, 0] * 50), max_ranges=3)
        self.assertEqual(report["changed_range_count"], 50)
        self.assertEqual(report["reported_range_count"], 3)
        self.assertEqual(report["changed_byte_span_total"], 50)
        self.assertTrue(report["ranges_truncated"])

    def test_hash_and_size_rejection_publish_nothing(self):
        output = self.root / "report.json"
        for expected in ("invalid", "0" * 64):
            result, _, err = self.cli("--expected-original-sha256", expected, "--json-out", output)
            self.assertEqual(result, 2)
            self.assertIn("SHA256", err)
            self.assertFalse(output.exists())
        self.modified.write_bytes(b"different length")
        self.assertEqual(self.cli("--fail-on-size-mismatch", "--json-out", output)[0], 2)
        self.assertFalse(output.exists())

    def test_valid_hash_case_and_opt_in_details(self):
        expected = hashlib.sha256(self.original.read_bytes()).hexdigest().lower()
        report = build_report(self.original, self.modified, expected, include_paths=True, include_previews=True)
        self.assertTrue(report["original"]["expected_sha256_match"])
        self.assertEqual(report["original"]["path"], str(self.original))
        self.assertEqual(report["changed_ranges"][0]["original_preview"], "01")

    def test_output_input_alias_and_existing_reports_never_overwrite(self):
        original = self.original.read_bytes()
        self.assertEqual(self.cli("--json-out", self.original)[0], 2)
        self.assertEqual(self.original.read_bytes(), original)
        output = self.root / "report.json"
        output.write_text("keep", encoding="utf-8")
        self.assertEqual(self.cli("--json-out", output)[0], 2)
        self.assertEqual(output.read_text(), "keep")

    def test_hardlink_output_never_overwrites_input(self):
        alias = self.root / "hardlinked-report.json"
        try:
            os.link(self.original, alias)
        except OSError as exc:
            self.skipTest(f"hard links unavailable: {exc}")
        self.assertEqual(self.cli("--json-out", alias)[0], 2)
        self.assertEqual(self.original.read_bytes(), b"\x00\x01\x02\x03")

    def test_output_collision_and_invalid_second_output_create_nothing(self):
        output = self.root / "report.json"
        self.assertEqual(self.cli("--json-out", output, "--markdown-out", output)[0], 2)
        self.assertFalse(output.exists())
        self.assertEqual(self.cli("--json-out", output, "--markdown-out", self.root / "absent" / "out.md")[0], 2)
        self.assertFalse(output.exists())

    def test_valid_outputs_and_deterministic_content(self):
        first, second = self.root / "report.json", self.root / "report.md"
        result, _, err = self.cli("--json-out", first, "--markdown-out", second)
        self.assertEqual((result, err), (0, ""))
        self.assertEqual(json.loads(first.read_text())["changed_byte_span_total"], 2)
        self.assertIn("not_flash_ready", second.read_text())
        self.assertEqual(build_report(self.original, self.modified), build_report(self.original, self.modified))

    def test_missing_inputs_limits_and_api_types(self):
        self.original.unlink()
        self.assertIn("existing regular file", self.cli()[2])
        self.original.write_bytes(b"four")
        self.assertEqual(self.cli("--max-input-bytes", 3)[0], 2)
        for value in (True, 0, -1, 1.5, 100001):
            with self.assertRaises(ValueError):
                changed_ranges(b"a", b"b", max_ranges=value)
        with self.assertRaises(TypeError):
            changed_ranges("a", b"b")

    def test_import_has_no_data_or_output_side_effects(self):
        with redirect_stdout(io.StringIO()) as out:
            import holden_wip.binary_diff as module
            importlib.reload(module)
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["modified data.bin", "original data.bin"])

    def test_api_privacy_and_size_flags_require_explicit_booleans(self):
        for value in ("false", "true", 0, 1, None):
            for name in ("include_paths", "include_previews", "fail_on_size_mismatch"):
                with self.subTest(flag=name, value=value), self.assertRaisesRegex(ValueError, "must be a boolean"):
                    build_report(self.original, self.modified, **{name: value})
            with self.assertRaisesRegex(ValueError, "must be a boolean"):
                changed_ranges(b"a", b"b", include_previews=value)

    def test_report_write_and_close_failure_roll_back_all_reservations(self):
        first, second = self.root / "first.json", self.root / "second.md"
        actual_open = Path.open

        class FailingStream:
            def __init__(self, inner):
                self.inner = inner

            def fileno(self):
                return self.inner.fileno()

            def write(self, content):
                return self.inner.write(content)

            def flush(self):
                raise OSError("injected write failure")

            def close(self):
                self.inner.close()
                raise OSError("injected close failure")

        def opening(path, *args, **kwargs):
            stream = actual_open(path, *args, **kwargs)
            return FailingStream(stream) if path == first else stream

        with patch.object(Path, "open", opening):
            with self.assertRaisesRegex(OSError, "injected write failure"):
                _write_reports([(first, "one"), (second, "two")], (self.original, self.modified))
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())

    def test_close_failure_after_writes_also_rolls_back(self):
        output = self.root / "close-failure.json"
        actual_open = Path.open

        class FailingClose:
            def __init__(self, inner):
                self.inner = inner

            def __getattr__(self, name):
                return getattr(self.inner, name)

            def close(self):
                self.inner.close()
                raise OSError("injected close-only failure")

        def opening(path, *args, **kwargs):
            return FailingClose(actual_open(path, *args, **kwargs))

        with patch.object(Path, "open", opening):
            with self.assertRaisesRegex(OSError, "injected close-only failure"):
                _write_reports([(output, "one")], ())
        self.assertFalse(output.exists())

    def test_cleanup_preserves_replacement_user_file(self):
        output, replacement = self.root / "replaced.json", self.root / "keep.json"
        replacement.write_text("user replacement", encoding="utf-8")
        actual_open = Path.open

        class ReplacedStream:
            def __init__(self, inner):
                self.inner = inner

            def __getattr__(self, name):
                return getattr(self.inner, name)

            def flush(self):
                self.inner.close()
                os.replace(replacement, output)
                raise OSError("injected replacement failure")

        def opening(path, *args, **kwargs):
            return ReplacedStream(actual_open(path, *args, **kwargs))

        with patch.object(Path, "open", opening):
            with self.assertRaisesRegex(OSError, "injected replacement failure"):
                _write_reports([(output, "report")], ())
        self.assertEqual(output.read_text(encoding="utf-8"), "user replacement")

    def test_markdown_optional_details_leave_tables_contiguous(self):
        report = build_report(self.original, self.modified, include_paths=True, include_previews=True)
        report["original"]["path"] = "<unsafe>|value"
        markdown = _markdown(report)
        lines = markdown.splitlines()
        original_row = next(i for i, line in enumerate(lines) if line.startswith("| original |"))
        self.assertTrue(lines[original_row + 1].startswith("| modified |"))
        range_row = lines.index("| `0x1` | `0x2` | 1 |")
        self.assertEqual(lines[range_row + 1], "| `0x3` | `0x4` | 1 |")
        self.assertGreater(lines.index("## Input paths"), range_row + 1)
        self.assertGreater(lines.index("## Byte previews"), range_row + 1)
        self.assertNotIn("<unsafe>", markdown)
        self.assertIn("&lt;unsafe&gt;", markdown)

    def test_cleanup_preserves_file_when_identity_is_unavailable(self):
        from types import SimpleNamespace
        output = self.root / "uncertain.json"
        actual_open = Path.open

        class FailingStream:
            def __init__(self, inner):
                self.inner = inner

            def __getattr__(self, name):
                return getattr(self.inner, name)

            def flush(self):
                raise OSError("injected publication failure")

        def opening(path, *args, **kwargs):
            return FailingStream(actual_open(path, *args, **kwargs))

        with patch.object(Path, "open", opening), patch("os.fstat", return_value=SimpleNamespace(st_dev=0, st_ino=0)):
            with self.assertRaisesRegex(OSError, "identity unavailable"):
                _write_reports([(output, "partial report")], ())
        self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
