# NEXUS Cervical Spine Criteria

A five-item, transparent implementation of the NEXUS low-risk cervical-spine decision instrument for patients with blunt trauma. It is intended for clinical education and decision support, not as a diagnosis or autonomous clearance system.

## Browser application

Open `web/index.html` from a local static HTTP server (for example, `python -m http.server 8080 --directory web`, then visit `http://localhost:8080`). The tool runs entirely in the browser with plain JavaScript; it does not require Python, an account, or an API. **No clinical responses are uploaded or retained** by this page. Do not enter patient identifiers. A public GitHub Pages address will be added only after the deployment is verified.

For each finding, select **Present**, **Absent**, or **Not assessed**:

1. Posterior midline cervical tenderness
2. Evidence of intoxication
3. Altered level of alertness
4. Focal neurological deficit
5. Painful distracting injury

**NEXUS negative:** All five findings absent; cervical-spine imaging may be unnecessary in the appropriate clinical context. **NEXUS positive:** At least one finding present; NEXUS does not support clinical clearance, but this does **not** diagnose injury. **Incomplete:** No positive finding, but one or more assessments missing; cannot clinically clear using NEXUS. Age is optional and is **not** a sixth NEXUS criterion; values below 16 or at least 65 trigger a caution concerning limited generalizability. Clinical judgment and local protocols always take precedence.

## Python CLI and CSV

A single-case evaluation uses the same named clinical findings:

```bash
python nexus_cspine.py single --midline-tenderness absent --intoxication absent --altered-alertness absent --focal-neurologic-deficit absent --distracting-injury absent
```

For multiple **de-identified** cases:

```bash
python nexus_cspine.py batch -i sample.csv -o results.csv
```

The CSV must include all five criterion columns exactly as shown in `sample.csv`. Values may be `present`/`absent`/`unknown`, `yes`/`no`, `true`/`false`, or `1`/`0`. Empty fields are treated as unassessed, never as negative. Free-text identifiers are copied into the output: the pattern-based PHI warning is **not** de-identification. Use synthetic or anonymized data only.

## API (optional)

```bash
pip install -e ".[dev]"
uvicorn agents.api:app --host 127.0.0.1 --port 8000
```

POST JSON booleans to `/api/nexus`. Fields may be omitted (yielding an incomplete assessment). Interactive documentation is available at `/docs`. A legacy **generic simulation** subsystem remains available via `nexus-c-spine-legacy` but is **not a NEXUS calculator**. Its HTTP endpoints are disabled by default; enable them only for trusted local development using `ENABLE_LEGACY_API=1` and a strong `LEGACY_API_TOKEN` supplied in an `X-API-Key` header. Do not place identifiable clinical data in legacy endpoints or audit logs.

## Testing and technology

```bash
python -m pytest
node --test web/test_core.mjs
```

Uses Python 3.10+, FastAPI/Pydantic (optional API), and native browser ES modules for the static interface. The browser requires a current modern desktop or mobile browser; no build step or Pyodide runtime is necessary. License: [MIT](LICENSE).

## Evidence and limitations

- Hoffman JR et al. *Validity of a set of clinical criteria to rule out injury to the cervical spine in patients with blunt trauma.* N Engl J Med. 2000;343:94–99. [doi:10.1056/NEJM200007133430203](https://doi.org/10.1056/NEJM200007133430203)
- ACR Appropriateness Criteria, *Acute Spinal Trauma* (revised 2024): [ACR criteria](https://acsearch.acr.org/docs/69359/Narrative)
- Moser N et al. *NEXUS criteria to rule out cervical spine injury among older patients: a systematic review.* [PMID:29232770](https://pubmed.ncbi.nlm.nih.gov/29232770/)

The instrument is not validated as a replacement for a complete trauma evaluation, and performance can differ in specific patient populations. This software has not undergone independent clinical validation or regulatory review.
