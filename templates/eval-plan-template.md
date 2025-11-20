# Evaluation Plan for [AGENT NAME]

## 1. Evaluation Requirements

<!--
ACTION REQUIRED: User input and interpreted evaluation requirements. Defaults to 1-2 key metrics if unspecified.
-->

- **User Input:** `"$ARGUMENTS"` or "No Input"
- **Interpreted Evaluation Requirements:** [Parsed from user input - highest priority]

---

## 2. Agent Analysis

| **Attribute**         | **Details**                                                 |
| :-------------------- | :---------------------------------------------------------- |
| **Agent Name**        | [Agent name]                                                |
| **Purpose**           | [Primary purpose and use case in 1-2 sentences]             |
| **Core Capabilities** | [Key functionalities the agent provides]                    |
| **Input**             | [Short description, Data types, schemas]                    |
| **Output**            | [Short description, Response types, schemas]                |
| **Agent Framework**   | [e.g., CrewAI, LangGraph, AutoGen, Custom/None]             |
| **Technology Stack**  | [Programming language, frameworks, libraries, dependencies] |

**Agent Architecture Diagram:**

```mermaid
[Mermaid diagram illustrating:
- Agent components and their relationships
- Data flow between components
- External integrations (APIs, databases, tools)
- User interaction points]
```

**Key Components:**

- **[Component Name 1]:** [Brief description of purpose and functionality]
- **[Component Name 2]:** [Brief description of purpose and functionality]
- [Additional components as needed]

**Available Tools:**

- **[Tool Name 1]:** [Purpose and usage]
- **[Tool Name 2]:** [Purpose and usage]
- [Additional tools as needed]

**Observability Status**

- **Tracing Framework** [Fully/Partially/Not Instrumented, Framework name, version]
- **Custom Attributes** [Yes/No, Key custom attributes if present]

---

## 3. Evaluation Metrics

<!--
ACTION REQUIRED: If no specific user requirements are provided, use a minimal number of metrics (1-2 metrics) focusing on the most critical aspects of agent performance.
-->

### [Metric Name 1]

- **Evaluation Area:** [Final response quailty/tool call accuracy/...]
- **Description:** [What is measured and why]
- **Method:** [Code-based | LLM-as-Judge ]

### [Metric Name 2]

[Repeat for each metric]

---

## 4. Test Data Generation

<!--
  ACTION REQUIRED: Keep scenarios minimal and focused. Do not propose more than 3 scenarios.
-->

- **[Test Scenario 1]**: [Description and purpose, complexity]
- **[Test scenario 2]**: [Description and purpose, complexity]
- **Total number of test cases**: [MUST be less than 3]

---

## 5. Evaluation Implementation Design

### 5.1 Evaluation Code Structure

<!--
ACTION REQUIRED: The code structure below will be adjusted based on your evaluation requirements and existing agent codebase. This is the recommended starting structure. Only adjust it if necessary.
-->

```Recommended evaluation code structure.
./                           # Repository root directory
├── requirements.txt         # Consolidated dependencies 
├── .venv/                   # Python virtual environment (created by uv)
│
└── eval/                    # Evaluation workspace
    ├── README.md            # Running instructions and usage examples (always present)
    ├── metrics.py           # Core evaluation metrics implementation (always present)
    ├── agent_runner.py      # Runs agent against test cases, agent execution logic (always present)
    ├── run_evaluation.py    # Main evaluation orchestration script (always present)
    ├── results/             # Evaluation outputs (always present)
    ├── eval-plan.md         # This evaluation specification and plan (always present)
    ├── test-cases.jsonl     # Generated test cases (from /evalkit.data)
    │
    └── traces/              # Processed trace files for evaluation (always present)
        └── <traceId>.json   # Individual processed trace files (from trace-processor.py)
```

### 5.2 Recommended Evaluation Technical Stack

| **Component**            | **Selection**                                          |
| :----------------------- | :----------------------------------------------------- |
| **Language/Version**     | [e.g., Python 3.11, Node.js 18+]                       |
| **Tracing Libraries**    | [e.g., Traceloop (default), Strands Telemetry (for Strands-based agents)]             |
| **OTEL Infrastructure**  | [Local collector with file export (default)]           |
| **Evaluation Libraries** | [e.g., DeepEval (default), RAGAS, Custom]              |
| **LLM Service**          | [LiteLLM (default)]                                    |
| **LLM Provider**         | [Bedrock (default)]                                    |
| **LLM Model**            | [us.anthropic.claude-sonnet-4-20250514-v1:0 (default)] |
| **Agent Integration**    | [e.g., Direct import, API]                             |
| **Results Storage**      | [e.g., JSON files (default)]                           |

---

## 6. Progress Tracking

### 6.1 User Requirements Log

| **Timestamp**      | **Source**      | **Requirement**                                                      |
| :----------------- | :-------------- | :------------------------------------------------------------------- |
| [YYYY-MM-DD HH:MM] | `/evalkit.plan` | [User input from $ARGUMENTS, or "No specific requirements provided"] |

### 6.2 Evaluation Progress

| **Timestamp**      | **Component**    | **Status**                      | **Notes**                                      |
| :----------------- | :--------------- | :------------------------------ | :--------------------------------------------- |
| [YYYY-MM-DD HH:MM] | [Component name] | [In Progress/Completed/Blocked] | [Technical details, blockers, or achievements] |
