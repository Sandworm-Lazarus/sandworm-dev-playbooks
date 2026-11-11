"""Verify local artifact hashes and declared result metadata without running commands."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


MAX_MANIFEST_BYTES = 1024 * 1024
MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
MAX_RESULT_BYTES = 256 * 1024
MAX_RECORDS = 1000
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class EvidenceError(ValueError):
    """Malformed manifest or unsafe local artifact reference."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("duplicate JSON object key")
        result[key] = value
    return result


def _json(raw):
    try:
        return json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise EvidenceError("invalid JSON document") from exc


def _text(value, label, maximum=128):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise EvidenceError(f"{label} must be a nonempty string of at most {maximum} characters")


def safe_path(root, declared):
    _text(declared, "artifact path", 512)
    if "\\" in declared or ":" in declared or "\x00" in declared:
        raise EvidenceError("artifact paths must be portable relative POSIX paths")
    relative = PurePosixPath(declared)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != declared or declared == ".":
        raise EvidenceError("absolute, escaping or noncanonical artifact path")
    try:
        resolved = (root / declared).resolve()
        resolved.relative_to(root)
    except (ValueError, OSError, RuntimeError) as exc:
        raise EvidenceError("artifact path or symlink escapes the root or cannot be resolved") from exc
    return resolved


def _command(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 64:
        raise EvidenceError("command must be a nonempty argument array of at most 64 strings")
    for item in value:
        _text(item, "command argument", 1024)


def validate_manifest(manifest, root):
    if not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise EvidenceError("manifest must be an object with schema_version 1")
    artifacts, commands = manifest.get("artifacts"), manifest.get("commands", [])
    if not isinstance(artifacts, list) or not 1 <= len(artifacts) <= MAX_RECORDS:
        raise EvidenceError(f"artifacts must contain from 1 to {MAX_RECORDS} records")
    if not isinstance(commands, list) or len(commands) > MAX_RECORDS:
        raise EvidenceError(f"commands must be an array of at most {MAX_RECORDS} records")
    paths = {}
    for item in artifacts:
        if not isinstance(item, dict):
            raise EvidenceError("each artifact must be an object")
        declared, digest = item.get("path"), item.get("sha256")
        resolved = safe_path(root, declared)
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise EvidenceError("artifact sha256 must contain 64 lowercase hexadecimal characters")
        if declared in paths:
            raise EvidenceError("duplicate artifact path")
        paths[declared] = resolved
    identifiers = set()
    for command in commands:
        if not isinstance(command, dict):
            raise EvidenceError("each command declaration must be an object")
        identifier = command.get("id")
        _text(identifier, "command id")
        if identifier in identifiers:
            raise EvidenceError("duplicate command id")
        identifiers.add(identifier)
        _command(command.get("command"))
        safe_path(root, command.get("result_path"))
        if command["result_path"] not in paths:
            raise EvidenceError("command result_path must reference a declared artifact")
        if type(command.get("expected_exit")) is not int or not -255 <= command["expected_exit"] <= 255:
            raise EvidenceError("expected_exit must be an integer from -255 to 255")
        _text(command.get("expected_result"), "expected_result")
    return paths


def _hash_artifact(path, keep_result):
    """Read bounded bytes once, hashing the same result bytes we later inspect."""
    digest, chunks, size = hashlib.sha256(), [], 0
    try:
        if not path.is_file():
            return "missing", None, None
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_ARTIFACT_BYTES or (keep_result and size > MAX_RESULT_BYTES):
                    return "too_large", None, None
                digest.update(chunk)
                if keep_result:
                    chunks.append(chunk)
    except OSError:
        return "unreadable", None, None
    return "read", digest.hexdigest(), b"".join(chunks) if keep_result else None


def verify(manifest, root):
    try:
        root = Path(root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise EvidenceError("root must be an existing directory") from exc
    if not root.is_dir():
        raise EvidenceError("root must be an existing directory")
    paths = validate_manifest(manifest, root)  # Validate all boundaries before reading artifacts.
    result_paths = {item["result_path"] for item in manifest.get("commands", [])}
    artifact_reports, statuses, result_bytes = [], {}, {}
    for artifact in manifest["artifacts"]:
        name = artifact["path"]
        status, digest, raw = _hash_artifact(paths[name], name in result_paths)
        if status == "read":
            status = "verified" if digest == artifact["sha256"] else "hash_mismatch"
        if status == "verified" and name in result_paths:
            result_bytes[name] = raw
        statuses[name] = status
        artifact_reports.append({"path": name, "status": status})
    command_reports = []
    for command in manifest.get("commands", []):
        record = {"id": command["id"]}
        path = command["result_path"]
        if statuses[path] != "verified":
            record["status"] = "unverified_result_artifact"
        else:
            try:
                observed = _json(result_bytes[path])
                if not isinstance(observed, dict) or type(observed.get("exit_code")) is not int:
                    raise EvidenceError("invalid result metadata")
                _text(observed.get("result"), "result")
                _command(observed.get("command"))
                record.update(
                    exit_matches=observed["exit_code"] == command["expected_exit"],
                    result_matches=observed["result"] == command["expected_result"],
                    command_matches=observed["command"] == command["command"],
                )
                record["status"] = "verified" if all(record[field] for field in ("exit_matches", "result_matches", "command_matches")) else "metadata_mismatch"
            except EvidenceError:
                record["status"] = "invalid_result_metadata"
        command_reports.append(record)
    return {
        "schema_version": 1,
        "ok": all(item["status"] == "verified" for item in artifact_reports + command_reports),
        "artifacts": artifact_reports, "commands": command_reports,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--root", default=Path("."), type=Path)
    args = parser.parse_args(argv)
    try:
        try:
            with args.manifest.open("rb") as stream:
                raw = stream.read(MAX_MANIFEST_BYTES + 1)
        except OSError as exc:
            raise EvidenceError("could not read manifest") from exc
        if len(raw) > MAX_MANIFEST_BYTES:
            raise EvidenceError("manifest exceeds the 1 MiB budget")
        report = verify(_json(raw), args.root)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["ok"] else 1
    except EvidenceError as exc:
        print(json.dumps({"error": str(exc), "ok": False, "status": "invalid_input"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
