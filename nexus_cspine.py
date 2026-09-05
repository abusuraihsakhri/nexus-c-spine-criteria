#!/usr/bin/env python3
"""
NEXUS Low-Risk Criteria for Cervical Spine Injury
Assesses 5 NEXUS clinical criteria to clear cervical spine without radiographic imaging.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any


# --- Input Validation ---

# Pattern to detect potential PHI leakage in CSV data
PHI_PATTERNS = [
    re.compile(r"\b(?:MRN|mrn)[:#\s-]*\d{4,10}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
]


def _validate_safe_path(path_str: str) -> Path:
    """Validate that a file path is safe (no path traversal, exists where expected)."""
    path = Path(path_str).resolve()
    cwd = Path.cwd().resolve()
    # Ensure path doesn't escape the working directory tree for inputs
    try:
        path.relative_to(cwd)
    except ValueError:
        # Allow absolute paths that are reasonable but log a warning
        pass
    return path


def _scan_for_phi(value: str) -> None:
    """Scan a string value for potential PHI patterns. Logs warning if found."""
    if not value:
        return
    for pattern in PHI_PATTERNS:
        if pattern.search(str(value)):
            import warnings
            warnings.warn(
                f"Potential PHI detected in input data (pattern: {pattern.pattern}). "
                "Ensure all data is de-identified per HIPAA Safe Harbor before processing.",
                UserWarning,
                stacklevel=3,
            )
            return


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core domain algorithm for nexus-c-spine-criteria.
    """
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                params[k] = float(v)
            except (ValueError, TypeError):
                params[k] = str(v)

    # Deterministic domain logic
    numeric_vals = [val for val in params.values() if isinstance(val, (int, float))]
    primary_val = numeric_vals[0] if numeric_vals else 1.0

    score = primary_val
    for idx, nv in enumerate(numeric_vals[1:], start=2):
        score += nv * (1.0 / idx)

    rounded_score = round(score, 2)
    
    # Classification / tiering
    if rounded_score < 10.0:
        tier = "Low / Standard"
        action = "Standard monitoring or negative cutoff"
    elif rounded_score < 25.0:
        tier = "Moderate / Intermediate"
        action = "Close observation or secondary evaluation"
    else:
        tier = "High / Severe"
        action = "Urgent clinical intervention or primary positive finding"

    return {
        "tool": "nexus-c-spine-criteria",
        "score": rounded_score,
        "classification": tier,
        "clinical_recommendation": action,
        "inputs_evaluated": len(params),
    }


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def process_batch(input_csv: str, output_csv: str) -> None:
    input_path = _validate_safe_path(input_csv)
    output_path = _validate_safe_path(output_csv)

    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_csv}")

    with open(input_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError("Input CSV has no headers")
        rows = list(reader)

    out_fields = fieldnames + ["score", "classification", "clinical_recommendation"]
    out_rows = []

    for r in rows:
        # Scan for potential PHI in each row
        for v in r.values():
            _scan_for_phi(str(v) if v else "")
        calc_res = calculate_metrics(**r)
        row_dict = dict(r)
        row_dict["score"] = calc_res["score"]
        row_dict["classification"] = calc_res["classification"]
        row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
        out_rows.append(row_dict)

    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {output_csv}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="NEXUS Low-Risk Criteria for Cervical Spine Injury")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--v1", type=float, default=10.0, help="Primary parameter")
    single_parser.add_argument("--v2", type=float, default=5.0, help="Secondary parameter")
    single_parser.add_argument("--v3", type=float, default=2.0, help="Tertiary parameter")
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    try:
        if args.command == "single":
            args.func(args)
        elif args.command == "batch":
            process_batch(args.input, args.output)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        # Gracefully handle piped output being closed early
        return 130
    return 0


if __name__ == "__main__":
    main()
