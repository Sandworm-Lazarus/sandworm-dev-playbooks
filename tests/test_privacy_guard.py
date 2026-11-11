"""Synthetic-data-only acceptance and rejection checks for the offline policy."""

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "privacy_guard.py"
SPEC = importlib.util.spec_from_file_location("privacy_guard", SCRIPT)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class PrivacyGuardTests(unittest.TestCase):
    def test_synthetic_policy_fixtures_and_idempotence(self):
        fixture = json.loads((ROOT / "examples" / "privacy-fixtures.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(fixture["cases"]), 6)
        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                policy = guard.Policy(sensitive_fields=guard.DEFAULT_SENSITIVE_FIELDS
                                      + tuple(case.get("sensitive_fields", [])))
                transform = guard.mask_json if case["mode"] == "json" else guard.mask_text
                result = transform(case["input"], policy)
                self.assertEqual(result, case["expected_output"])
                self.assertEqual(transform(result, policy), result)

    def test_json_is_recursive_deterministic_and_does_not_mutate_input(self):
        original = {"z": ["dev@example.invalid", {"api_key": "SYNTHETIC"}], "a": 4}
        saved = copy.deepcopy(original)
        self.assertEqual(guard.mask_json(original),
                         {"a": 4, "z": [guard.EMAIL_MASK, {"api_key": guard.FIELD_MASK}]})
        self.assertEqual(original, saved)
        first = guard.redact_json_text(json.dumps(original))
        second = guard.redact_json_text(json.dumps(dict(reversed(list(original.items())))))
        self.assertEqual(first, second)
        self.assertEqual(guard.redact_json_text(first), first)

    def test_unconfigured_names_phone_numbers_and_keys_are_preserved(self):
        value = {"person@example.invalid": "บุคคลสมมติ", "phone": "+00-000-SYNTHETIC",
                 "api_key_hint": "example", " api_key": "example"}
        self.assertEqual(guard.mask_json(value), value)

    def test_python_api_can_replace_default_field_policy(self):
        policy = guard.Policy(sensitive_fields=("private_note",))
        self.assertEqual(guard.mask_json({"PASSWORD": "synthetic", "PRIVATE_NOTE": 12}, policy),
                         {"PASSWORD": "synthetic", "PRIVATE_NOTE": guard.FIELD_MASK})

    def test_policy_names_are_normalized_deterministically(self):
        self.assertEqual(guard.Policy(sensitive_fields=("Z", "a", "A")).sensitive_fields,
                         ("a", "z"))

    def test_unrecognized_mailbox_forms_are_outside_scope(self):
        # No RFC quoted local parts, single-label hosts or internationalized local parts.
        for text in ('"a b"@example.invalid', "dev@localhost", "ผู้ใช้@example.invalid"):
            with self.subTest(text=text):
                self.assertEqual(guard.mask_text(text), text)

    def test_text_preserves_whitespace_and_unicode(self):
        text = "  ติดต่อ dev@example.invalid\n\tภาษาไทย  "
        self.assertEqual(guard.mask_text(text), "  ติดต่อ [EMAIL_REDACTED]\n\tภาษาไทย  ")

    def test_existing_masks_remain_unchanged(self):
        value = {"password": guard.FIELD_MASK, "note": guard.EMAIL_MASK}
        self.assertEqual(guard.mask_json(value), value)

    def test_root_json_types_remain_supported(self):
        for value in (None, True, False, 2, 1.25, "example", [], {}):
            with self.subTest(kind=type(value).__name__):
                self.assertEqual(guard.mask_json(value), value)

    def test_utf8_budget_counts_bytes_and_accepts_exact_boundary(self):
        self.assertEqual(guard.mask_text("ก", guard.Policy(max_bytes=3)), "ก")
        with self.assertRaises(guard.PrivacyError):
            guard.mask_text("ก", guard.Policy(max_bytes=2))

    def test_compact_json_budget_counts_keys_quotes_and_escapes(self):
        for text in ('{}', '"\\n"', '{"x":0}'):
            with self.subTest(text=text):
                size = len(text.encode("utf-8"))
                self.assertEqual(guard.redact_json_text(text, guard.Policy(max_bytes=size)), text)
                with self.assertRaises(guard.PrivacyError):
                    guard.mask_json(json.loads(text), guard.Policy(max_bytes=size - 1))

    def test_output_expansion_is_rejected_before_success(self):
        with self.assertRaises(guard.PrivacyError):
            guard.mask_text("a@b.invalid", guard.Policy(max_bytes=11))
        with self.assertRaises(guard.PrivacyError):
            guard.mask_json({"password": 0}, guard.Policy(max_bytes=14))

    def test_text_exact_mask_budget_remains_idempotent(self):
        policy = guard.Policy(max_bytes=len(guard.EMAIL_MASK))
        result = guard.mask_text("a@b.invalid", policy)
        self.assertEqual(guard.mask_text(result, policy), result)

    def test_depth_zero_allows_only_root_values_and_empty_containers(self):
        policy = guard.Policy(max_depth=0)
        for value in (None, "hello", [], {}):
            self.assertEqual(guard.mask_json(value, policy), value)
        for value in ([None], {"value": None}):
            with self.assertRaises(guard.PrivacyError):
                guard.mask_json(value, policy)

    def test_depth_boundary_and_parser_preflight(self):
        policy = guard.Policy(max_depth=2)
        self.assertEqual(guard.mask_json([[0]], policy), [[0]])
        for text in ("[[[0]]]", "[" * 10000 + "]" * 10000):
            with self.assertRaises(guard.PrivacyError):
                guard.redact_json_text(text, policy)

    def test_quoted_brackets_do_not_count_as_nesting(self):
        self.assertEqual(guard.redact_json_text('"[[[{\\\"x\\\"}]]]"', guard.Policy(max_depth=0)),
                         '"[[[{\\\"x\\\"}]]]"')

    def test_node_budget_boundary(self):
        within = [None] * (guard.MAX_NODES - 1)
        self.assertEqual(len(guard.mask_json(within)), len(within))
        with self.assertRaises(guard.PrivacyError):
            guard.mask_json([None] * guard.MAX_NODES)

    def test_cycles_are_rejected_but_shared_subtrees_are_supported(self):
        cyclic = []
        cyclic.append(cyclic)
        with self.assertRaises(guard.PrivacyError):
            guard.mask_json(cyclic)
        shared = ["demo@example.invalid"]
        self.assertEqual(guard.mask_json([shared, shared]), [[guard.EMAIL_MASK], [guard.EMAIL_MASK]])

    def test_invalid_sensitive_subtree_is_not_silently_discarded(self):
        with self.assertRaises(guard.PrivacyError):
            guard.mask_json({"password": {"bad": {1, 2}}})
        with self.assertRaises(guard.PrivacyError):
            guard.mask_json({"password": [[0]]}, guard.Policy(max_depth=1))

    def test_unsupported_python_types_and_nonstring_keys_are_rejected(self):
        for value in (b"synthetic", (1, 2), {1, 2}, object(), {1: "value"}):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises(guard.PrivacyError):
                    guard.mask_json(value)

    def test_nonfinite_numbers_are_rejected(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.assertRaises(guard.PrivacyError):
                guard.mask_json(value)
        for text in ("NaN", "Infinity", "-Infinity", "1e9999", '{"password":NaN}'):
            with self.assertRaises(guard.PrivacyError):
                guard.redact_json_text(text)

    def test_integer_conversion_has_an_explicit_portable_limit(self):
        within = "9" * guard.MAX_INTEGER_DIGITS
        self.assertEqual(guard.redact_json_text(within), within)
        for value in (10 ** guard.MAX_INTEGER_DIGITS, -(10 ** guard.MAX_INTEGER_DIGITS)):
            with self.assertRaises(guard.PrivacyError):
                guard.mask_json(value)
        with self.assertRaises(guard.PrivacyError):
            guard.redact_json_text("9" * (guard.MAX_INTEGER_DIGITS + 1))

    def test_duplicate_keys_and_malformed_json_are_rejected(self):
        for text in ('{"password":"synthetic", "password":"other"}', "", "{} {}", "[1,]", "{broken"):
            with self.subTest(text=text):
                with self.assertRaises(guard.PrivacyError):
                    guard.redact_json_text(text)

    def test_unpaired_surrogates_are_rejected(self):
        for action in (lambda: guard.mask_text("\ud800"),
                       lambda: guard.mask_json({"x": "\udfff"}),
                       lambda: guard.redact_json_text('"\\ud800"')):
            with self.assertRaises(guard.PrivacyError):
                action()

    def test_invalid_policy_is_rejected_without_echoing_values(self):
        policies = ({"max_bytes": 0}, {"max_bytes": True},
                    {"max_bytes": guard.HARD_MAX_BYTES + 1}, {"max_depth": -1},
                    {"max_depth": guard.HARD_MAX_DEPTH + 1},
                    {"sensitive_fields": "SYNTHETIC-SECRET"}, {"sensitive_fields": ("",)},
                    {"sensitive_fields": (1,)}, {"sensitive_fields": ("x" * 129,)},
                    {"sensitive_fields": tuple(str(i) for i in range(129))})
        for settings in policies:
            with self.subTest(settings=settings):
                with self.assertRaises(guard.PrivacyError) as caught:
                    guard.Policy(**settings)
                self.assertNotIn("SYNTHETIC-SECRET", str(caught.exception))
        with self.assertRaises(guard.PrivacyError):
            guard.mask_text("hello", policy={})


class PrivacyGuardCLITests(unittest.TestCase):
    def run_cli(self, *arguments, data=b""):
        return subprocess.run([sys.executable, str(SCRIPT), *arguments], input=data,
                              capture_output=True, timeout=10)

    def assert_rejected(self, result, marker=b"SYNTHETIC-SECRET"):
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertNotIn(marker, result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)

    def test_text_stdin_has_no_extra_newline(self):
        result = self.run_cli("text", data=b"to dev@example.invalid")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"to [EMAIL_REDACTED]")
        self.assertEqual(result.stderr, b"")

    def test_json_cli_fields_extend_defaults_and_output_is_stable(self):
        result = self.run_cli("json", "--sensitive-field", "private",
                              data=b'{"private":123,"password":"SYNTHETIC","safe":true}')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'{"password":"[FIELD_REDACTED]","private":"[FIELD_REDACTED]","safe":true}')
        again = self.run_cli("json", "--sensitive-field", "private", data=result.stdout)
        self.assertEqual(again.stdout, result.stdout)

    def test_cli_exact_byte_boundaries_reprocess_without_newline_growth(self):
        for raw in (b"{}", b"0", b"true", b'""'):
            with self.subTest(raw=raw):
                result = self.run_cli("json", "--max-bytes", str(len(raw)), data=raw)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, raw)
                again = self.run_cli("json", "--max-bytes", str(len(raw)), data=result.stdout)
                self.assertEqual(again.returncode, 0)
                self.assertEqual(again.stdout, result.stdout)

    def test_file_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "synthetic.json"
            source.write_text('{"note":"tester@example.invalid"}', encoding="utf-8")
            result = self.run_cli("json", "--input", str(source))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout), {"note": guard.EMAIL_MASK})

    def test_empty_text_is_valid_and_empty_json_is_rejected(self):
        result = self.run_cli("text")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        self.assert_rejected(self.run_cli("json"))

    def test_validation_errors_do_not_echo_raw_input(self):
        for raw in (b'{"password":"SYNTHETIC-SECRET",',
                    b'{"SYNTHETIC-SECRET":1,"SYNTHETIC-SECRET":2}',
                    b'{"password":NaN}', b'"\\ud800"', b"\xff"):
            with self.subTest(raw=raw):
                self.assert_rejected(self.run_cli("json", data=raw))

    def test_budget_errors_emit_no_partial_transformation(self):
        self.assert_rejected(self.run_cli("text", "--max-bytes", "3", data=b"SYNTHETIC-SECRET"))
        self.assert_rejected(self.run_cli("text", "--max-bytes", "11", data=b"a@b.invalid"))
        self.assert_rejected(self.run_cli("json", "--max-depth", "1", data=b'[["SYNTHETIC-SECRET"]]'))

    def test_argument_errors_do_not_echo_unknown_or_invalid_values(self):
        self.assert_rejected(self.run_cli("SYNTHETIC-SECRET"))
        self.assert_rejected(self.run_cli("text", "--SYNTHETIC-SECRET"))
        self.assert_rejected(self.run_cli("text", "--max-bytes", "SYNTHETIC-SECRET"))

    def test_io_failure_has_distinct_status_and_hides_path(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("json", "--input", str(Path(directory) / "SYNTHETIC-SECRET"))
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, b"")
        self.assertNotIn(b"SYNTHETIC-SECRET", result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
