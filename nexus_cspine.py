#!/usr/bin/env python3
"""Five-item NEXUS cervical-spine low-risk decision instrument.

Research/education implementation. Not a substitute for clinical judgment.
Reference: Hoffman et al. N Engl J Med. 2000;343:94-99.
DOI: 10.1056/NEJM200007133430203
"""

import argparse
import csv
import json
import os
import tempfile
import re
import sys
import warnings
from pathlib import Path
from typing import Any, Dict

CRITERIA = (
    "midline_tenderness",
    "intoxication",
    "altered_alertness",
    "focal_neurologic_deficit",
    "distracting_injury",
)
PHI_PATTERNS = (
    re.compile(r"\bMRN[:#\s-]*\d{4,10}\b", re.I),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
)


def _validate_safe_path(path_str: str) -> Path:
    """Resolve an explicit local path; this does not impose a filesystem sandbox."""
    return Path(path_str).expanduser().resolve()


def _scan_for_phi(value: str) -> None:
    """Best-effort warning only; NOT de-identification or a PHI guarantee."""
    if value and any(pattern.search(str(value)) for pattern in PHI_PATTERNS):
        warnings.warn("Possible patient identifier in CSV; use de-identified data only.", UserWarning, stacklevel=2)


def _parse_finding(value: Any) -> bool | None:
    """True = finding PRESENT, False = finding ABSENT, None = not assessed."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("", "unknown", "not assessed", "na", "n/a"):
            return None
        if lowered in ("true", "yes", "present", "1"):
            return True
        if lowered in ("false", "no", "absent", "0"):
            return False
    if type(value) is int and value in (0, 1):
        return bool(value)
    raise ValueError(f"Invalid criterion response {value!r}; use present/absent/unknown")


def calculate_metrics(**kwargs: Any) -> Dict[str, Any]:
    """Evaluate all five NEXUS findings; never infer unassessed negatives.

    The five arguments named in CRITERIA are required for a negative result.
    Unknown/missing answers yield INCOMPLETE unless a positive is present.
    Positive means the rule cannot support clinical clearance, NOT diagnosed injury.
    """
    extras = set(kwargs) - set(CRITERIA) - {"age"}
    if extras:
        raise ValueError(f"Unknown clinical fields: {', '.join(sorted(extras))}")
    findings = {name: _parse_finding(kwargs.get(name)) for name in CRITERIA}
    positive = [name for name, value in findings.items() if value is True]
    missing = [name for name, value in findings.items() if value is None]
    age = kwargs.get("age")
    if age not in (None, ""):
        try:
            age_value = int(age)
        except (ValueError, TypeError) as exc:
            raise ValueError("Age must be a whole number") from exc
        if str(age).strip() != str(age_value) or not 0 <= age_value <= 120:
            raise ValueError("Age must be an integer from 0 to 120")
        age = age_value
    else:
        age = None

    if positive:
        classification = "NEXUS_POSITIVE"
        recommendation = "NEXUS does not support clinical clearance; assess need for cervical-spine imaging."
        negative = False
    elif missing:
        classification = "INCOMPLETE"
        recommendation = "Complete all five assessments; do not clear cervical spine using this incomplete rule."
        negative = None
    else:
        classification = "NEXUS_NEGATIVE"
        recommendation = "All five low-risk criteria met; imaging may be unnecessary if clinically appropriate."
        negative = True

    caution = ("Evidence is less certain in children and adults aged 65 or older; "
               "do not rely on this tool alone.") if age is not None and (age < 16 or age >= 65) else None
    return {
        "tool": "nexus-c-spine-criteria",
        "classification": classification,
        "nexus_negative": negative,
        "positive_criteria": positive,
        "missing_criteria": missing,
        "criteria": findings,
        "clinical_recommendation": recommendation,
        "age_caution": caution,
        "disclaimer": "Decision support for qualified clinicians; not a diagnosis or substitute for clinical judgment.",
    }


def process_single(args: argparse.Namespace) -> None:
    print(json.dumps(calculate_metrics(**{name: getattr(args, name) for name in CRITERIA}, age=args.age), indent=2))


def _safe_csv_cell(value: Any) -> Any:
    """Neutralize spreadsheet formulas in non-clinical CSV columns on export."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def process_batch(input_csv: str, output_csv: str) -> int:
    """Stream clinical rows and atomically replace output only on success."""
    source, destination = _validate_safe_path(input_csv), _validate_safe_path(output_csv)
    if source == destination:
        raise ValueError("Input and output files must be different")
    if not source.is_file():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    count = 0
    temporary_path = None
    try:
        with source.open(newline="", encoding="utf-8-sig") as src:
            reader = csv.DictReader(src)
            fields = reader.fieldnames
            if not fields:
                raise ValueError("Input CSV has no headers")
            if len(set(fields)) != len(fields):
                raise ValueError("Duplicate CSV column headers")
            missing = [name for name in CRITERIA if name not in fields]
            if missing:
                raise ValueError("Missing NEXUS columns: " + ", ".join(missing))
            result_columns = (
                "classification", "nexus_negative", "positive_criteria",
                "missing_criteria", "clinical_recommendation", "age_caution",
            )
            output_fields = list(fields) + [col for col in result_columns if col not in fields]
            with tempfile.NamedTemporaryFile(
                "w", newline="", encoding="utf-8", dir=destination.parent,
                prefix=".nexus-", suffix=".tmp", delete=False,
            ) as dest:
                temporary_path = Path(dest.name)
                writer = csv.DictWriter(dest, fieldnames=output_fields)
                writer.writeheader()
                for row_number, row in enumerate(reader, start=2):
                    if None in row:
                        raise ValueError(f"CSV row {row_number}: more cells than headers")
                    for value in row.values():
                        _scan_for_phi(str(value or ""))
                    try:
                        result = calculate_metrics(
                            **{name: row[name] for name in CRITERIA}, age=row.get("age")
                        )
                    except ValueError as exc:
                        raise ValueError(f"CSV row {row_number}: {exc}") from exc
                    row.update({
                        "classification": result["classification"],
                        "nexus_negative": "" if result["nexus_negative"] is None else str(result["nexus_negative"]).lower(),
                        "positive_criteria": ";".join(result["positive_criteria"]),
                        "missing_criteria": ";".join(result["missing_criteria"]),
                        "clinical_recommendation": result["clinical_recommendation"],
                        "age_caution": result["age_caution"] or "",
                    })
                    writer.writerow({key: _safe_csv_cell(value) for key, value in row.items()})
                    count += 1
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return count


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="NEXUS cervical-spine low-risk rule (blunt trauma)")
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Evaluate one clinical assessment")
    for criterion in CRITERIA:
        single.add_argument("--" + criterion.replace("_", "-"), choices=("present", "absent", "unknown"), required=True)
    single.add_argument("--age", type=int, help="Optional patient age, used only for interpretation caution")
    batch = commands.add_parser("batch", help="Process a de-identified clinical CSV")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            process_single(args)
        else:
            print(f"Processed {process_batch(args.input, args.output)} records -> {args.output}")
    except (ValueError, FileNotFoundError, OSError, csv.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
