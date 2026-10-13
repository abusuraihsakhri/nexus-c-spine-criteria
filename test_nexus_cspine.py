from nexus_cspine import CRITERIA, calculate_metrics

def test_clinical_nexus_negative():
    result = calculate_metrics(**{key: "absent" for key in CRITERIA})
    assert result["classification"] == "NEXUS_NEGATIVE"
    assert result["nexus_negative"] is True
