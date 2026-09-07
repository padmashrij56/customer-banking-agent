<div align="center">

# 🏦 Enterprise Loan Underwriting Platform

### Bootcamp 3 · Building a Production-Ready Multi-Agent Loan Underwriting Platform

*A guided project for operationalizing a Planner-orchestrated, five-agent loan underwriting workflow — integrated with the Model Context Protocol, observed via LangSmith, validated by automated tests, and packaged for deployment.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4%20via%20OpenRouter-412991?logo=openai&logoColor=white)](https://openrouter.ai/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-6E56CF)](https://modelcontextprotocol.io/)
[![LangSmith](https://img.shields.io/badge/LangSmith-Tracing-1C3C3C)](https://smith.langchain.com/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-0467DF)](https://github.com/facebookresearch/faiss)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![pytest](https://img.shields.io/badge/pytest-Smoke%20Suite-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Status](https://img.shields.io/badge/Status-Starter%20Solution-yellow)](#-project-status)

</div>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Start Here](#-start-here)
- [Quick Start](#-quick-start)
- [Project Structure](#️-project-structure)
- [What You'll Build](#-what-youll-build)
- [Technology Stack](#️-technology-stack)
- [Learning Objectives](#-learning-objectives)
- [Testing](#-testing)
- [Reference Solution](#-reference-solution)
- [Project Status](#-project-status)
- [Support](#-support)
- [Next Steps](#-next-steps)

---

## 🎯 Overview

This project simulates Phase 3 of a retail bank's Enterprise AI programme: taking a
prototype-grade multi-agent pattern and making it **production-ready**. You extend an
existing platform with an orchestration-and-operations layer that a loan officer can trust.

| Capability                               | Description                                                                                                                                             |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🧭**Planner-driven orchestration** | A`PlannerAgent` builds a fixed, linear five-step plan; an `AgentCoordinator` executes it against the specialist agents                              |
| 🧩**Specialist coordination**      | Five provided agents — customer profile, credit risk, compliance, lending policy, recommendation — aggregated into one result via a shared`context` |
| 🔌**Standardized tool access**     | One enterprise capability (credit bureau lookup) exposed and consumed over the Model Context Protocol                                                   |
| 🔍**Observability**                | A full Planner run wrapped in LangSmith tracing from a single entry point                                                                               |
| ✅**Structural validation**        | A`WorkflowValidator` checks a workflow result's shape before it is returned                                                                           |
| 🧪**Automated testing**            | A pytest smoke suite covering plan, registry, and validator behavior — no API key required                                                             |
| 📦**Containerization**             | The platform packaged and run as one reproducible Docker image                                                                                          |

> [!NOTE]
> **Prerequisite:** Bootcamp 2 (Enterprise Customer Service Operations Platform) completed.
> This project reuses BC1/BC2's generic infrastructure pattern (`src/llm/`, `src/utils/`,
> `src/knowledge/`) and config-driven engineering discipline without re-explaining them.

---

## 📚 Start Here

> [!IMPORTANT]
> 👉 Run **[`app/workbook_app.py`](app/workbook_app.py)** — the interactive guided workbook.
> It is the single, self-contained entry point for the entire lab: business context,
> concepts, the exact method(s) to implement highlighted live from your own file,
> step-by-step instructions, and a one-click Run/Validate per activity. Do not start with
> any other file.

```bash
streamlit run app/workbook_app.py
```

**8 hands-on activities across 3 phases**, each validated before you move on.
**⏱️ Estimated completion time:** ~3 hours.

---

## 🚀 Quick Start

### Prerequisites

- 🐍 Python 3.10 or higher
- 🔑 An OpenRouter API key — on your lab desktop, double-click the **Lab Details** icon; it
  opens a page with your OpenRouter account's API key and a copy button
- 🐳 Docker — **Activity 3.2 only**. If `docker --version` fails, install it (step 4 below).
  Activities 1.1–3.1 don't need it.

### Setup

<details open>
<summary><b>1. Install dependencies</b></summary>

```bash
pip install -r requirements.txt
```

</details>

<details open>
<summary><b>2. Configure environment</b></summary>

```bash
cp .env.example .env
# Edit .env and paste the API key from the Lab Details icon into OPENAI_API_KEY.
# .env.example is preset for OpenRouter (LLM_BASE_URL + provider-namespaced model names).
```

</details>

<details open>
<summary><b>3. Launch the workbook</b></summary>

```bash
streamlit run app/workbook_app.py
```

</details>

<details>
<summary><b>4. Install Docker — only if you'll do Activity 3.2</b></summary>

First check whether it's already there:

```bash
docker --version && docker compose version
```

If that fails on **Ubuntu / Debian** (the standard lab desktop), install Docker Engine +
the Compose plugin:

```bash
# official convenience script — installs Docker Engine + Compose, enables the daemon
curl -fsSL https://get.docker.com | sudo sh

# verify (the daemon is already started by the script)
sudo docker run --rm hello-world
```

**Just use `sudo docker …` / `sudo docker compose …` for the session** — that always works
and is fine for Activity 3.2. To drop the `sudo`, add yourself to the `docker` group and
open a **new terminal** (or `exec su -l "$USER"`) so the group takes effect:

```bash
sudo usermod -aG docker "$USER"
# then, in a fresh shell:
docker run --rm hello-world
```

If you hit `permission denied … /var/run/docker.sock`, your shell hasn't picked up the
group yet — use `sudo`, a new shell, or `sudo chmod 666 /var/run/docker.sock` (lab-only).

No `sudo` at all? Ask your lab administrator, or use **Podman** — it's a drop-in here:
`podman build -t loan-underwriting-platform .` and `podman compose up`.

The containerized portal publishes on **host port 8502** (→ container 8501), so it runs
alongside the workbook app / a local `streamlit run` on 8501 without a clash. Open
**http://localhost:8502** once `docker compose up` is running.

> If Docker can't be installed in your environment, Activity 3.2 becomes read-and-understand
> (the `Dockerfile` and `docker-compose.yml` are provided, complete), so the rest of the lab
> is unaffected.

</details>

> [!IMPORTANT]
> Run every command from the **project root** — the workbook app, the portal, and the
> source modules all resolve `data/` and `config/` paths relative to it.

---

## 🏗️ Project Structure

```
app/workbook_app.py             # the guided lab - start here (Streamlit): 8 activities,
                                 # live code hints, one-click Run/Validate per activity
app/streamlit_app.py            # Enterprise Loan Underwriting Portal (provided, complete)
src/
  agents/                       # 5 specialist agents (provided) + planner_agent.py (TODO)
  core/                         # agent_coordinator.py, workflow_validator.py (TODO)
  mcp/                          # mcp_server.py, mcp_client.py (TODO)
  observability/                # tracing.py (TODO)
  services/                     # loan_application_service.py, credit_score_service.py (TODO)
  knowledge/                    # RAG components, reused from BC1/BC2 (provided)
  llm/                          # LLM client + prompt manager, reused from BC1/BC2 (provided)
  utils/                        # logging, config, validators, reused from BC1/BC2 (provided)
data/
  knowledge_base/loans/         # reused from BC1/BC2 (Lending Policy Agent's RAG source)
  business_data/                # mock loan applications, credit scores
  validation/                   # test scenarios
config/                         # agent / llm / prompts / mcp YAML config
tests/test_workflow.py          # pytest smoke suite (TODO)
reference_solution/src/         # completed implementations, mirroring src/'s TODO modules
reference_solution/tests/       # completed test_workflow.py (Activity 3.1)
Dockerfile, docker-compose.yml  # provided, complete (Activity 3.2)

```

> [!TIP]
> Everything in `src/` marked with `TODO` / `raise NotImplementedError` is what **you**
> implement during the guided lab. `reference_solution/` holds the completed version for
> comparison — try each activity yourself before peeking.

---

## 🔍 What You'll Build

| Layer               | Component                                                                                       | You implement?                               |
| ------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------- |
| Presentation        | `app/streamlit_app.py`                                                                        | No — provided, complete                     |
| Orchestration       | `src/agents/planner_agent.py`                                                                 | **Yes** (Activity 1.2)                 |
| Coordination        | `src/core/agent_coordinator.py`                                                               | **Yes** (Activity 1.3)                 |
| Reasoning           | `src/agents/{customer_profile,credit_risk,compliance,lending_policy,recommendation}_agent.py` | No — 5 specialist agents, provided complete |
| Enterprise Services | `src/services/loan_application_service.py`, `src/services/credit_score_service.py`          | **Yes** (Activity 1.2)                 |
| Protocol Access     | `src/mcp/mcp_server.py`, `src/mcp/mcp_client.py`                                            | **Yes** (Activity 2.1)                 |
| Observability       | `src/observability/tracing.py`                                                                | **Yes** (Activity 2.2)                 |
| Validation          | `src/core/workflow_validator.py`                                                              | **Yes** (Activity 2.3)                 |
| Testing             | `tests/test_workflow.py`                                                                      | **Yes** (Activity 3.1)                 |
| Deployment          | `Dockerfile`, `docker-compose.yml` (provided)                                                 | Build & run the container (Activity 3.2)     |

### By phase

| Phase                                                     | Focus                                                                                                     | Activities                                                                                                |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Phase 1 — Planner-Driven Orchestration**         | Stand up the Planner/Coordinator pattern that drives every application through the five specialist agents | 1.1 Explore · 1.2 Implement the Planner Agent · 1.3 Coordinate Specialized AI Agents                    |
| **Phase 2 — Protocol, Observability & Validation** | A standardized tool interface over MCP, traceable runs in LangSmith, and self-checked output              | 2.1 Integrate MCP · 2.2 Enable LangSmith Observability · 2.3 Validate Multi-Agent Workflows             |
| **Phase 3 — Testing & Containerization**           | An automated test suite, and the platform running inside a Docker container                               | 3.1 Implement Automated Testing · 3.2 Containerize the Platform                                         |

---

## 🛠️ Technology Stack

| Component          | Technology                                                                                               |
| :----------------- | :------------------------------------------------------------------------------------------------------- |
| 🐍 Language        | Python 3.10+                                                                                             |
| 🔗 LLM access      | `openai` Python SDK (2.x) against an OpenAI-compatible Chat Completions API                            |
| 🤖 LLM provider    | OpenRouter, model`openai/gpt-4` via `LLM_BASE_URL` (a direct OpenAI key with no base URL also works) |
| 🕸️ Orchestration | Planner/Coordinator in plain Python — no agent framework                                                |
| 🔌 Tool protocol   | Model Context Protocol (`mcp` — `FastMCP` server, `ClientSession` over stdio)                     |
| 🔍 Observability   | LangSmith (`langsmith.traceable`), two env vars, one wrapped entry point                               |
| 🗂️ Vector store  | FAISS (`faiss-cpu`), knowledge base reused from BC1/BC2                                                |
| 🧪 Testing         | pytest smoke suite (structural, no network)                                                              |
| 📦 Packaging       | Docker + Docker Compose                                                                                  |
| 🖥️ UI            | Streamlit — the Loan Underwriting Portal and the guided workbook app                                    |
| ⚙️ Configuration | YAML (`config/*.yaml`) + `.env` via `python-dotenv`                                                |

---

## 🎓 Learning Objectives

By completing this bootcamp, you will be able to:

- [X] Design a production-ready multi-agent architecture
- [X] Implement a planner-driven orchestration pattern (plan, then execute)
- [X] Integrate one enterprise tool via the Model Context Protocol, server and client
- [X] Monitor a multi-agent workflow with LangSmith tracing
- [X] Validate multi-agent behavior structurally, both in-workflow and via automated tests
- [X] Containerize an enterprise AI application
- [X] Apply the modular, config-driven engineering discipline from BC1/BC2 to a production-operations context

---

## 🧪 Testing

The lab ships a small, fixed pytest smoke suite. It checks plan/registry/validator **shape**,
not LLM output — none of it calls the real API, so it runs without any credentials.

```bash
pytest tests/test_workflow.py -v
```

Activity 3.1 asks you to implement three of its five tests; the other two are prefilled
structural checks. `python scripts/verify_reference.py` independently verifies the reference
solution (pytest against a merged copy, an in-process pipeline run with the API mocked, and a
real MCP stdio round-trip).

---

## 📦 Reference Solution

`reference_solution/` holds the completed versions of what each activity produces:
`src/` (the TODO modules) and `tests/test_workflow.py` (Activity 3.1). It does **not**
duplicate other shared assets (data, config, docs, the Streamlit app) that already exist once
in the main project. Do not open it before attempting each activity yourself — see it only if
you're stuck after a genuine attempt.

---

## 📝 Project Status

**Current Status:** 🟡 Starter Solution

| Component                                                                             |                                            Status                                            |
| :------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------: |
| Project structure & configuration                                                     |                                            ✅ Done                                            |
| Infrastructure reused from BC1/BC2 (`src/llm/`, `src/knowledge/`, `src/utils/`) |                                            ✅ Done                                            |
| 5 specialist agents + Streamlit portal                                                |                                     ✅ Provided, complete                                     |
| Planner / Coordinator orchestration                                                   |                                🔨 To be implemented (Phase 1)                                |
| MCP tool, LangSmith tracing, Workflow Validator                                       |                                🔨 To be implemented (Phase 2)                                |
| pytest suite, container run                                                           |                                🔨 To be implemented (Phase 3)                                |
| Reference solution                                                                    |                            ✅ Implemented & independently verified                            |
| Guided workbook app (`app/workbook_app.py`)                                         | ✅ One-click Run/Validate per activity; degrades gracefully against the unimplemented starter |

---

## 🤝 Support

- Reference solution available in [`reference_solution/`](reference_solution/) for comparison
- `python scripts/verify_reference.py` — end-to-end verification harness for the reference implementation

---

## 📄 License

This is an educational project for the Agentic AI for Enterprise Delivery Bootcamp.

---

## 🎯 Next Steps

1. ⚙️ Follow the [Quick Start](#-quick-start) to configure your environment
2. ▶️ Run `streamlit run app/workbook_app.py` and begin with Activity 1.1
3. 🚀 Build the orchestration layer, one validated activity at a time

<div align="center">

**Good luck and happy building! 🚀**

</div>
