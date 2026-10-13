"""Regression tests for clinical input validation, PHI heuristics and audit integrity."""
import warnings

import pytest

from agents.base import AuditTrail, PHIGuard, SecurityException
from nexus_cspine import CRITERIA, _scan_for_phi, calculate_metrics, process_batch


def test_phi_guard_rejects_obvious_identifiers():
    for value in ("Patient MRN-123456", "123-45-6789", "name@example.com"):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi(value)


def test_phi_redaction_is_best_effort():
    assert "MRN-123456" not in PHIGuard.redact_phi("MRN-123456")


def test_audit_detects_modified_signed_entries():
    trail = AuditTrail(secret_key="test-only-key")
    trail.log("actor", "tier", "EVT", {"key": "one"})
    trail.log("actor", "tier", "EVT", {"key": "two"})
    assert trail.verify_integrity()
    trail.logs[0]["event_type"] = "FORGED"
    assert not trail.verify_integrity()


def test_no_static_fallback_secret(monkeypatch):
    monkeypatch.delenv("AUDIT_SECRET_KEY", raising=False)
    with pytest.warns(RuntimeWarning, match="ephemeral"):
        trail = AuditTrail()
    assert trail.secret_key


def test_phi_csv_warning():
    with pytest.warns(UserWarning, match="identifier"):
        _scan_for_phi("MRN-1234567")


def test_invalid_clinical_value_rejected():
    inputs = {name: "absent" for name in CRITERIA}
    inputs["intoxication"] = "ambiguous"
    with pytest.raises(ValueError):
        calculate_metrics(**inputs)


def test_missing_file_and_headers(tmp_path):
    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "missing.csv"), str(tmp_path / "out.csv"))
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    with pytest.raises(ValueError, match="no headers"):
        process_batch(str(empty), str(tmp_path / "out.csv"))
