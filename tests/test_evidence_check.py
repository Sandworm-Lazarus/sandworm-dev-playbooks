"""Integrity, path-boundary and no-execution regressions for evidence checking."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/evidence_check.py"
SPEC = importlib.util.spec_from_file_location("evidence_check", SCRIPT)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "root"
        self.root.mkdir()
        (self.root / "artifact.txt").write_text("synthetic artifact\n", encoding="utf-8")
        self.record = {"command": ["synthetic-check"], "exit_code": 0, "result": "passed"}
        self.result = self.root / "result.json"
        self.result.write_text(json.dumps(self.record), encoding="utf-8")
        self.manifest = {
            "schema_version": 1,
            "artifacts": [{"path": "artifact.txt", "sha256": digest(self.root / "artifact.txt")},
                          {"path": "result.json", "sha256": digest(self.result)}],
            "commands": [{"id": "check", "command": ["synthetic-check"], "result_path": "result.json",
                          "expected_exit": 0, "expected_result": "passed"}],
        }

    def test_committed_fabricated_manifest_and_deterministic_report(self):
        manifest = json.loads((ROOT / "examples/evidence-manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(checker.verify(manifest, ROOT)["ok"])
        self.assertEqual(checker.verify(self.manifest, self.root), checker.verify(self.manifest, self.root))

    def test_changed_and_missing_artifacts_fail(self):
        (self.root / "artifact.txt").write_text("changed\n", encoding="utf-8")
        report = checker.verify(self.manifest, self.root)
        self.assertFalse(report["ok"])
        self.assertEqual(report["artifacts"][0]["status"], "hash_mismatch")
        (self.root / "artifact.txt").unlink()
        self.assertEqual(checker.verify(self.manifest, self.root)["artifacts"][0]["status"], "missing")

    def test_exit_result_and_command_metadata_are_independently_compared(self):
        for field, changed, flag in (
            ("exit_code", 1, "exit_matches"), ("result", "failed", "result_matches"),
            ("command", ["different-check"], "command_matches"),
        ):
            with self.subTest(field=field):
                observed = dict(self.record, **{field: changed})
                self.result.write_text(json.dumps(observed), encoding="utf-8")
                manifest = copy.deepcopy(self.manifest)
                manifest["artifacts"][1]["sha256"] = digest(self.result)
                command = checker.verify(manifest, self.root)["commands"][0]
                self.assertEqual(command["status"], "metadata_mismatch")
                self.assertFalse(command[flag])

    def test_unverified_or_invalid_result_is_not_accepted(self):
        self.result.write_text("not json", encoding="utf-8")
        self.assertEqual(checker.verify(self.manifest, self.root)["commands"][0]["status"], "unverified_result_artifact")
        self.manifest["artifacts"][1]["sha256"] = digest(self.result)
        self.assertEqual(checker.verify(self.manifest, self.root)["commands"][0]["status"], "invalid_result_metadata")

    def test_unsafe_paths_reject_whole_manifest_before_artifact_reads(self):
        for path in ("../outside.txt", "/etc/passwd", "C:/outside.txt", "a/../artifact.txt", "./artifact.txt", "a\\b", "a//b"):
            with self.subTest(path=path):
                manifest = copy.deepcopy(self.manifest)
                manifest["artifacts"][1]["path"] = path
                with patch.object(checker, "_hash_artifact", side_effect=AssertionError("must not read")):
                    with self.assertRaises(checker.EvidenceError):
                        checker.verify(manifest, self.root)

    def test_file_and_directory_symlink_escapes_are_rejected(self):
        outside = self.base / "private.txt"
        outside.write_text("SYNTHETIC_SECRET_MUST_NOT_BE_PRINTED", encoding="utf-8")
        try:
            (self.root / "link.txt").symlink_to(outside)
            (self.root / "linked-directory").symlink_to(self.base, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable")
        for path in ("link.txt", "linked-directory/private.txt"):
            manifest = {"schema_version": 1, "artifacts": [{"path": path, "sha256": "0" * 64}]}
            with self.subTest(path=path), self.assertRaises(checker.EvidenceError):
                checker.verify(manifest, self.root)

    def test_command_is_only_metadata_and_source_contents_are_not_returned(self):
        marker = self.root / "must-not-exist"
        command = ["sh", "-c", "touch " + str(marker)]
        self.result.write_text(json.dumps(dict(self.record, command=command)), encoding="utf-8")
        self.manifest["artifacts"][1]["sha256"] = digest(self.result)
        self.manifest["commands"][0]["command"] = command
        report = checker.verify(self.manifest, self.root)
        self.assertTrue(report["ok"])
        self.assertFalse(marker.exists())
        serialized = json.dumps(report)
        self.assertNotIn("touch", serialized)
        self.assertNotIn("synthetic artifact", serialized)
        self.assertNotIn('"passed"', serialized)

    def test_duplicates_bad_hashes_boolean_exit_and_budget_are_rejected(self):
        for modify in (
            lambda m: m["artifacts"].append(copy.deepcopy(m["artifacts"][0])),
            lambda m: m["commands"].append(copy.deepcopy(m["commands"][0])),
            lambda m: m["artifacts"][0].update(sha256="wrong"),
            lambda m: m["commands"][0].update(expected_exit=True),
            lambda m: m["commands"][0].update(result_path="undeclared.json"),
        ):
            manifest = copy.deepcopy(self.manifest)
            modify(manifest)
            with self.assertRaises(checker.EvidenceError):
                checker.verify(manifest, self.root)
        with patch.object(checker, "MAX_ARTIFACT_BYTES", 1):
            self.assertEqual(checker.verify(self.manifest, self.root)["artifacts"][0]["status"], "too_large")
        with self.assertRaises(checker.EvidenceError):
            checker._json(b'{"schema_version":1,"schema_version":1}')

    def test_cli_returns_verification_failure_and_validation_error(self):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(self.manifest), encoding="utf-8")
        base = [sys.executable, str(SCRIPT), "--manifest", str(path), "--root", str(self.root)]
        good = subprocess.run(base, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertTrue(json.loads(good.stdout)["ok"])
        (self.root / "artifact.txt").unlink()
        self.assertEqual(subprocess.run(base, capture_output=True).returncode, 1)
        self.manifest["artifacts"][0]["path"] = "../unsafe"
        path.write_text(json.dumps(self.manifest), encoding="utf-8")
        bad = subprocess.run(base, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(json.loads(bad.stdout)["status"], "invalid_input")


if __name__ == "__main__":
    unittest.main()
