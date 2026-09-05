# NEXUS C Spine Criteria

> **Domain:** Diagnostic Radiology & Medical Imaging AI
> **Reference Guidelines & Standards:** `American College of Radiology (ACR) RADS & Fleischner Society`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

NEXUS Low-Risk Criteria for Cervical Spine Injury. Assesses 5 NEXUS clinical criteria to clear cervical spine without radiographic imaging.

Zero-dependency Python implementation with single and batch evaluation.

Author: Dr. Abu Suraih Sakhri | License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_metrics(**kwargs)`** — Core scoring algorithm that computes a weighted score from clinical parameters and returns classification/recommendation.
- **`process_single(args)`** — Evaluates a single case from CLI arguments.
- **`process_batch(input_csv, output_csv)`** — Processes batch CSV records with PHI scanning and path validation.
- **`main()`** — CLI entry point with subcommands (`single`, `batch`).

### 🏗️ Architecture (`agents/` package)

| Module | Purpose |
|--------|---------|
| `supervisor.py` | Multi-worker orchestrator that coordinates evaluation and produces consensus dossiers |
| `workers.py` | Specialized domain workers (QC Invariant, Safety Escalation, Protocol Conformance) |
| `base.py` | HMAC-SHA256 tamper-evident audit trail, PHI guard, security exceptions |
| `models.py` | Pydantic v2 data models for tasks, alerts, dossiers, urgency levels |
| `llm_factory.py` | Pluggable LLM adapter (mock, Ollama, Claude, OpenAI) |
| `api.py` | FastAPI REST server with `/health`, `/metrics`, `/api/audit`, `/api/chat` endpoints |
| `metrics.py` | Prometheus-format metrics exporter |
| `learning.py` | Bayesian calibration engine for worker reliability tracking |
| `streamer.py` | WebSocket telemetry broadcaster |

---

## 💻 CLI Quickstart & Usage

### Installation

```bash
pip install -e ".[dev]"
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env and set a strong AUDIT_SECRET_KEY:
#   python -c "import secrets; print(secrets.token_hex(32))"
```

### 1. Single Case Evaluation

```bash
python nexus_cspine.py single --v1 12.0 --v2 4.0 --v3 1.5
```

### 2. Batch CSV Processing

```bash
python nexus_cspine.py batch -i sample.csv -o results.csv
```

### 3. Enterprise CLI (Full Feature Set)

```bash
# Audit task
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Chat query
python cli.py chat "Explain the NEXUS criteria thresholds"

# Verify audit trail
python cli.py verify-audit

# Launch REST server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | De-identified patient identifier | Required |
| `v1` | Primary clinical parameter | Required |
| `v2` | Secondary clinical parameter | Required |
| `v3` | Tertiary clinical parameter | Optional |

---

## 🛡️ Security & Enterprise Architecture

- **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers in all outbound data.
- **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation. Key sourced from `AUDIT_SECRET_KEY` environment variable.
- **Input Validation:** Batch processing validates file paths and scans for potential PHI patterns in CSV data.
- **FastAPI REST API:** OpenAPI 3.1 endpoints with health checks and audit log access.
- **Active Learning Calibration:** Bayesian worker reliability tracking with Brier score monitoring.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput simulation benchmarks:

```bash
python simulator.py 1000
```

Run from the enterprise CLI:

```bash
python cli.py verify-audit
```

---

## 🐳 Container Deployment

### Docker Compose (Recommended)

```bash
cp .env.example .env
# Set AUDIT_SECRET_KEY in .env
docker compose up --build
```

### Manual Docker

```bash
docker build -t nexus-c-spine-criteria .
docker run -p 8000:8000 --env-file .env nexus-c-spine-criteria
```

---

## 📁 Project Structure

```
nexus-c-spine-criteria/
├── agents/                 # Enterprise agent package
│   ├── __init__.py         # Package metadata (v3.0.0-ENTERPRISE)
│   ├── supervisor.py       # Multi-worker orchestrator
│   ├── workers.py          # Domain evaluation workers
│   ├── base.py             # Security, audit, PHI guard
│   ├── models.py           # Pydantic data models
│   ├── api.py              # FastAPI REST server
│   ├── metrics.py          # Prometheus exporter
│   ├── learning.py         # Bayesian calibration
│   ├── llm_factory.py      # LLM adapter factory
│   └── streamer.py         # WebSocket telemetry
├── tests/                  # Test suite
│   ├── test_nexus_c_spine_criteria.py
│   └── test_enrichment.py
├── web/index.html          # Operations dashboard UI
├── cli.py                  # Enterprise CLI entry point
├── nexus_cspine.py         # Core algorithm + simple CLI
├── enrichment.py           # Enrichment feature engines
├── simulator.py            # High-throughput testing simulator
├── pyproject.toml          # Python package metadata & dependencies
├── Dockerfile              # Container build definition
├── docker-compose.yml      # Multi-service orchestration
├── .env.example            # Environment template
└── sample.csv              # Example batch input data
```
