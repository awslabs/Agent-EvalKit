# Evaluation Plan for [AGENT NAME]

## 1. Evaluation Requirements

[Brief description of the evaluation requirements provided by users. If no specific requirements are provided, this will default to a minimal evaluation setup with one or two most important metric.]

---

## 2. Agent Overview

## 2. Agent Analysis

| **Attribute**  | **Details**                                            |
| :------------- | :----------------------------------------------------- |
| **Name**       | [Agent name]                                           |
| **Purpose**    | [Primary purpose in 1-2 sentences]                     |
| **Tech Stack** | [Languages, frameworks, key dependencies]              |
| **Tools**      | [List tool names - REQUIRED for tool coverage metrics] |
| **Tracing**    | [Fully/Partially/Not Instrumented - framework name]    |

**Architecture:**

```mermaid
[Diagram showing components, data flow, and key interactions]
```

**Input/Output:**

- **Input:** [Data types, schemas]
- **Output:** [Response types, schemas]

---

## 3. Evaluation Metrics

### [Metric Name 1]

- **Area:** [Performance/Quality/Reliability/Safety/Cost]
- **Description:** [What is measured and why]
- **Method:** [Algorithmic | LLM-as-Judge | Hybrid]
- **Scale:** [e.g., 0-10, binary, percentage]
- **Target:** [Acceptable threshold]

**Rubric:** _(For LLM-as-Judge)_

- **9-10 (Excellent):** [Specific criteria]
- **7-8 (Good):** [Clear expectations]
- **5-6 (Acceptable):** [Minimum standards]
- **3-4 (Poor):** [Substandard indicators]
- **1-2 (Fail):** [Critical failures]

### [Metric Name 2]

[Repeat for each metric]

---

## 4. Implementation

### Code Structure

```
./
├── requirements.txt
├── .venv/
└── eval/
    ├── README.md
    ├── eval-plan.md
    ├── metrics.py
    ├── agent_runner.py         # [if needed]
    ├── run_evaluation.py
    ├── test-scenarios.jsonl
    ├── traces/
    │   └── <traceId>.json
    └── results/
        └── report.md
```

### Technical Stack

| **Component**    | **Technology**                   |
| :--------------- | :------------------------------- |
| **Language**     | [e.g., Python 3.11+]             |
| **Tracing**      | [e.g., Traceloop, OpenTelemetry] |
| **Evaluation**   | [e.g., DeepEval (default)]       |
| **LLM Gateway**  | [e.g., LiteLLM (default)]        |
| **LLM Provider** | [e.g., Bedrock (default)]        |
| **LLM Model**    | [e.g., claude-sonnet-4]          |
| **Integration**  | [Direct import/API/CLI]          |

### Evaluation Flow

```mermaid
[Pipeline: Data → Agent → Traces → Metrics → Report]
```

**Run Command:**

```bash
[e.g., python eval/run_evaluation.py]
```

---

## 5. Test Data

**Scenarios:**

- **[Category 1]:** [Count] test cases, [Simple/Medium/Complex]
- **[Category 2]:** [Count] test cases, [Simple/Medium/Complex]

**Format:**

```json
{
  "id": "[unique-id]",
  "category": "[category]",
  "input": "[agent input]",
  "expected_output": "[optional]",
  "metadata": { "complexity": "[level]", "tags": ["[tag]"] }
}
```

---

## 6. Progress Log

### Requirements

- **[YYYY-MM-DD HH:MM]** – `/evalkit.plan`: [User input or "No input"]

### Decisions

- **[YYYY-MM-DD HH:MM]** – [Decision: rationale]

### Implementation

- **[YYYY-MM-DD HH:MM]** – [Component: status, notes]

---

_Living document - update as evaluation progresses_
