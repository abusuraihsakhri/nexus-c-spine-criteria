"""Executable checks for published NEXUS logical interpretation."""
import json
from pathlib import Path
import pytest
from nexus_cspine import CRITERIA, calculate_metrics

BENCHMARK = json.loads((Path(__file__).parent.parent / "benchmark_dataset.json").read_text())


@pytest.mark.parametrize("case", BENCHMARK["test_cases"], ids=lambda c: c["case_id"])
def test_benchmark_classification(case):
    values = dict(zip(CRITERIA, case["findings"]))
    assert calculate_metrics(**values)["classification"] == case["expected"]
