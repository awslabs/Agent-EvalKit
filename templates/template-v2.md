# Evaluation Plan Specification

## Evaluation Requirement

[This section breifly describe the evluation requirement from users through the evaluation process. If no input at al, then it's will be default minimal evaluation setup. ]

## Agent Analysis and Overview

### Agent Information

- **Agent Name:** [The agent name]
- **Brief Description:** [Purpose & core capabilities in 1-2 sentences]
- **Technology Stack:** [Languages, frameworks, key dependencies]

### Agent Architecture & Components

- **System Architecture:**
  \`\`\`mermaid
  [Draw a Mermaid diagram showing agent components, data flow, and key interactions]
  \`\`\`

- **Key Components/Sub-Agents:** [If applicable, list major components or sub-agents with brief descriptions]
- **Input/Output Formats:** [Data types, schemas, interaction patterns]
- **Tools Available:** [If applicable, list tool names with brief descriptions - REQUIRED for tool coverage metrics]
- **Tracing Status:** [Fully/Partially/Not Instrumented by which tracing framework - tracing libraries found]
- **Key Decision Points:** [If applicable, list critical decision points where agent makes choices or reasoning steps]

---

## Evaluation Metric Design

### [Metric Name 1]

- **Evaluation Area:** [Brief description of the target evaluation area]
- **Description:** [Clear definition of what is measured and why]
- **Computation Method:** [Choose: Algorithmic | LLM-as-Judge | Hybrid] + [brief methodology]
- **Scale:** [e.g., 0-10 continuous, 1-10 discrete, binary pass/fail]
- **Success Criteria:** [Target values or thresholds for acceptable performance]
- **Evaluation Rubric:** _(For LLM-as-Judge metrics)_
  - **Excellent (9-10):** [Specific criteria for top performance]
  - **Good (7-8):** [Clear expectations for good performance]
  - **Acceptable (5-6):** [Minimum acceptable standards]
  - **Poor (3-4):** [Indicators of poor performance]
  - **Fail (1-2):** [Complete failure criteria]

### [Metric Name 2]

...

---

## Evaluation Implementation Design

### Evaluation Code Architecture

- **Description:** [Brief explanation of the evaluation system design]
- **Evaluation Flow:**
  \`\`\`mermaid
  [Mermaid diagram showing evaluation pipeline, data flow, and component interactions]
  \`\`\`

### Evaluation Code Structure

[ Add the code structure here.
You need to adjust the structure based on evaluation requirements and existing agent code.
The following is the recommended evaluation code structure.
]

```Recommended evaluation code structure.
./                           # Repository root directory
├── requirements.txt         # Consolidated dependencies (created by /evalkit.trace, updated by /evalkit.code)
├── .venv/                   # Python virtual environment (created by uv)
│
└── eval/                    # Evaluation workspace
    ├── README.md            # Running instructions and usage examples (always present)
    ├── metrics.py           # Core evaluation metrics implementation (always present)
    ├── agent_runner.py      # Runs agent against test scenarios (if needed)
    ├── run_evaluation.py    # Main evaluation orchestration script (always present)
    ├── results/             # Evaluation outputs (always present)
    ├── eval-plan.md         # This evaluation specification and plan (always present)
    ├── test-scenarios.jsonl  # Generated test scenarios (from /evalkit.data)
    │
    └── traces/              # Processed trace files for evaluation
        └── <traceId>.json   # Individual processed trace files (from trace-processor.py)
```

### Recommended Evaluation Technical Stack

| **Component**            | **Selection**                                          |
| :----------------------- | :----------------------------------------------------- |
| **Language/Version**     | [e.g., Python 3.11, Node.js 18+]                       |
| **Tracing Libraries**    | [e.g., Traceloop (default), OpenTelemetry]             |
| **OTEL Infrastructure**  | [Local collector with file export (default)]           |
| **Evaluation Libraries** | [e.g., DeepEval (default), RAGAS, Custom]              |
| **LLM Service**          | [LiteLLM (default)]                                    |
| **LLM Provider**         | [Bedrock (default)]                                    |
| **LLM Model**            | [us.anthropic.claude-sonnet-4-20250514-v1:0 (default)] |
| **Agent Integration**    | [e.g., Direct import, API]                             |
| **Results Storage**      | [e.g., JSON files (default)]                           |

---

## Test Data Generation

---

## Progress Notes

### User Requirement Inputs.

- **YYYY-MM-DD HH:MM** – - `/evalkit.plan`: [User input from $ARGUMENTS, or "No Input"]

### Design Decisions Log

- **YYYY-MM-DD HH:MM** – [Decision made, rationale, alternatives considered]

### Implementation Notes

- **YYYY-MM-DD HH:MM** – [Progress update, technical decisions, blockers resolved]

---

`
