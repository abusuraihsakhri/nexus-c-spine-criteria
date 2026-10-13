"""Clinical-rule regression tests against the five-item NEXUS definition."""
import csv
from pathlib import Path
import pytest
from nexus_cspine import CRITERIA, calculate_metrics, process_batch, main

ABSENT = {name: "absent" for name in CRITERIA}


def test_all_absent_is_negative():
    result = calculate_metrics(**ABSENT)
    assert result["nexus_negative"] is True
    assert result["classification"] == "NEXUS_NEGATIVE"


@pytest.mark.parametrize("criterion", CRITERIA)
def test_any_positive_blocks_clearance(criterion):
    result = calculate_metrics(**{**ABSENT, criterion: "present"})
    assert result["classification"] == "NEXUS_POSITIVE"
    assert result["positive_criteria"] == [criterion]


def test_unknown_fails_closed():
    result = calculate_metrics(**{**ABSENT, "intoxication": "unknown"})
    assert result["classification"] == "INCOMPLETE"
    assert result["nexus_negative"] is None


def test_positive_with_unknown_is_not_incomplete_or_negative():
    result = calculate_metrics(**{**ABSENT, "intoxication": "present", "distracting_injury": "unknown"})
    assert result["classification"] == "NEXUS_POSITIVE"


@pytest.mark.parametrize("value", ["maybe", 3, 2.0, [], {}, "2"])
def test_invalid_findings_rejected(value):
    with pytest.raises(ValueError):
        calculate_metrics(**{**ABSENT, "intoxication": value})


def test_no_numeric_shortcut_or_unknown_fields():
    with pytest.raises(ValueError, match="Unknown clinical fields"):
        calculate_metrics(v1=10)


def test_age_warning():
    assert "65" in calculate_metrics(**ABSENT, age=70)["age_caution"]
    assert calculate_metrics(**ABSENT, age=30)["age_caution"] is None


def test_batch_with_clinical_headers(tmp_path: Path):
    inp, out = tmp_path / "input.csv", tmp_path / "output.csv"
    with inp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case_id", *CRITERIA])
        writer.writeheader()
        writer.writerow({"case_id": "Case-1", **ABSENT})
        writer.writerow({"case_id": "Case-2", **{**ABSENT, "intoxication": "present"}})
    assert process_batch(str(inp), str(out)) == 2
    with out.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["classification"] for r in rows] == ["NEXUS_NEGATIVE", "NEXUS_POSITIVE"]


def test_batch_rejects_missing_headers(tmp_path: Path):
    inp = tmp_path / "invalid.csv"
    inp.write_text("ID,v1,v2\nP001,5,3\n")
    with pytest.raises(ValueError, match="Missing NEXUS columns"):
        process_batch(str(inp), str(tmp_path / "output.csv"))


def test_batch_rejects_same_path(tmp_path: Path):
    inp = tmp_path / "in.csv"
    inp.write_text(",".join(CRITERIA) + "\n")
    with pytest.raises(ValueError, match="different"):
        process_batch(str(inp), str(inp))


def test_cli_error_on_incomplete_arguments():
    with pytest.raises(SystemExit) as result:
        main(["single", "--midline-tenderness", "absent"])
    assert result.value.code == 2


def test_batch_fails_without_partial_output(tmp_path: Path):
    inp, out = tmp_path / "in.csv", tmp_path / "out.csv"
    header = ",".join(CRITERIA)
    inp.write_text(f"{header}\nabsent,absent,absent,absent,absent\nabsent,INVALID,absent,absent,absent\n")
    out.write_text("PREVIOUS RESULTS")
    with pytest.raises(ValueError, match="row 3"):
        process_batch(str(inp), str(out))
    assert out.read_text() == "PREVIOUS RESULTS"
    assert not list(tmp_path.glob(".nexus-*.tmp"))


def test_csv_spreadsheet_injection_escaped(tmp_path: Path):
    inp, out = tmp_path / "in.csv", tmp_path / "out.csv"
    inp.write_text("case_id," + ",".join(CRITERIA) + "\n=1+1," + ",".join(["absent"] * 5) + "\n")
    process_batch(str(inp), str(out))
    with out.open(newline="") as h:
        row = next(csv.DictReader(h))
    assert row["case_id"] == "'=1+1"
