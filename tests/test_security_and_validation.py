"""
Automated tests for security and validation improvements.
"""
import sys
import warnings
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import AuditTrail, AuditLogger, PHIGuard, SecurityException
from nexus_cspine import _validate_safe_path, _scan_for_phi, process_batch, main


class TestPHIGuardEnforcement:
    """PHI Guard correctly blocks sensitive identifiers."""

    def test_mrn_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-994827")

    def test_ssn_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phone_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call (555) 123-4567")

    def test_email_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("patient@hospital.org")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("NEXUS criteria evaluation complete")

    def test_empty_string_passes(self):
        PHIGuard.assert_no_phi("")

    def test_none_passes(self):
        PHIGuard.assert_no_phi(None)

    def test_redact_phi(self):
        redacted = PHIGuard.redact_phi("Contact patient MRN-12345678 immediately")
        assert "MRN-12345678" not in redacted
        assert "[REDACTED_IDENTIFIER]" in redacted


class TestAuditTrailSecurity:
    """Audit trail does not use hardcoded fallback keys."""

    def test_no_hardcoded_default_key(self):
        """When no key is provided, a random ephemeral key should be generated."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            trail = AuditTrail()
            assert len(w) == 1
            assert "AUDIT_SECRET_KEY not set" in str(w[0].message)
            assert issubclass(w[0].category, RuntimeWarning)

    def test_key_from_env_var(self, monkeypatch):
        monkeypatch.setenv("AUDIT_SECRET_KEY", "test-key-from-env")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            trail = AuditTrail()
            assert len(w) == 0  # No warning when env var is set

    def test_key_from_argument(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            trail = AuditTrail(secret_key="direct-test-key")
            assert len(w) == 0  # No warning when key is passed directly

    def test_audit_integrity_verification(self):
        trail = AuditTrail(secret_key="test-integrity-key")
        trail.log("test-actor", "test-tier", "TEST_EVENT", {"data": "value1"})
        trail.log("test-actor", "test-tier", "TEST_EVENT", {"data": "value2"})
        assert trail.verify_integrity() is True
        assert len(trail.get_trail()) == 2


class TestBatchValidation:
    """Batch processing validates inputs correctly."""

    def test_missing_file_raises_error(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))

    def test_empty_csv_raises_error(self, tmp_path):
        empty = tmp_path / "empty.csv"
        empty.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="no headers"):
            process_batch(str(empty), str(tmp_path / "out.csv"))

    def test_valid_batch_processing(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text("ID,v1,v2\nP001,10.0,5.0\nP002,20.0,8.0\n", encoding="utf-8")

        process_batch(str(csv_in), str(csv_out))

        assert csv_out.exists()
        content = csv_out.read_text(encoding="utf-8")
        assert "P001" in content
        assert "P002" in content
        assert "score" in content

    def test_phi_scanning_in_batch(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text(
            "ID,v1,v2\nP001-MRN-12345678,10.0,5.0\n",
            encoding="utf-8"
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            process_batch(str(csv_in), str(csv_out))
            # Should warn about PHI
            phi_warnings = [x for x in w if "PHI" in str(x.message)]
            assert len(phi_warnings) >= 1

    def test_main_returns_error_on_missing_file(self):
        result = main(["batch", "-i", "/nonexistent/path.csv"])
        assert result == 1

    def test_main_returns_success_on_valid_single(self):
        result = main(["single", "--v1", "10.0"])
        assert result == 0

    def test_safe_path_validation(self, tmp_path):
        # Valid path within cwd should work
        result = _validate_safe_path(str(tmp_path / "test.csv"))
        assert isinstance(result, Path)


class TestInputValidationHelpers:
    """Input validation helper functions."""

    def test_scan_phi_detects_mrn(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _scan_for_phi("Patient MRN-12345678")
            assert len(w) == 1
            assert "PHI" in str(w[0].message)

    def test_scan_phi_detects_ssn(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _scan_for_phi("123-45-6789")
            assert len(w) == 1

    def test_scan_phi_ignores_clean_text(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _scan_for_phi("NEXUS criteria evaluation")
            phi_warnings = [x for x in w if "PHI" in str(x.message)]
            assert len(phi_warnings) == 0

    def test_scan_phi_handles_empty(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _scan_for_phi("")
            phi_warnings = [x for x in w if "PHI" in str(x.message)]
            assert len(phi_warnings) == 0
