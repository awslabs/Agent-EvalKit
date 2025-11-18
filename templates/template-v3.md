# Evaluation Plan for [AGENT NAME]

## 1. Evaluation Requirements

[Brief description of the evaluation requirements provided by users. If no specific requirements are provided, this will default to a minimal evaluation setup with one or two most important metric.]

---

## 2. Agent Analysis

### 2.1 Agent Overview

| **Attribute**         | **Details**                                                 |
| :-------------------- | :---------------------------------------------------------- |
| **Agent Name**        | [Agent name]                                                |
| **Purpose**           | [Primary purpose and use case in 1-2 sentences]             |
| **Core Capabilities** | [Key functionalities the agent provides]                    |
| **Technology Stack**  | [Programming language, frameworks, libraries, dependencies] |
| **Version**           | [Agent version if applicable]                               |

### 2.2 Agent Architecture

**System Architecture Diagram:**

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

### 2.3 Agent Capabilities

**Input/Output Specifications:**

- **Input Format:** [Data types, schemas, expected structure]
- **Output Format:** [Response types, schemas, structure]
- **Interaction Pattern:** [Synchronous/Asynchronous, streaming, batch]

**Available Tools:** [REQUIRED for tool coverage metrics]

- **[Tool Name 1]:** [Purpose and usage]
- **[Tool Name 2]:** [Purpose and usage]
- [Additional tools as needed]

**Decision Points:** [Critical reasoning or choice points in agent workflow]

- **[Decision Point 1]:** [Context and significance]
- **[Decision Point 2]:** [Context and significance]

### 2.4 Observability Status

| **Aspect**            | **Status**                         | **Details**                        |
| :-------------------- | :--------------------------------- | :--------------------------------- |
| **Tracing Framework** | [Fully/Partially/Not Instrumented] | [Framework name, version]          |
| **Custom Attributes** | [Yes/No]                           | [Key custom attributes if present] |

---

## 3. Evaluation Metrics

### 3.1 Metric: [Metric Name 1]

**Overview:**

- **Evaluation Area:** [Performance/Quality/Reliability/Safety/Cost/etc.]
- **Description:** [Clear definition of what this metric measures and its importance]
- **Rationale:** [Why this metric is relevant for this agent]

**Measurement Specification:**

- **Computation Method:** [Algorithmic | LLM-as-Judge | Hybrid]
- **Methodology:** [Detailed explanation of how the metric is calculated]
- **Data Sources:** [Traces/Logs/Direct outputs/User feedback]
- **Scale:** [e.g., 0-1 continuous, 1-10 discrete, binary pass/fail, percentage]
- **Unit:** [If applicable: seconds, tokens, dollars, etc.]

**Success Criteria:**

- **Target Value:** [Ideal performance level]
- **Acceptable Threshold:** [Minimum acceptable performance]
- **Critical Threshold:** [Below this indicates serious issues]

**Evaluation Rubric:** _(Required for LLM-as-Judge metrics)_

| **Score Range** | **Level**  | **Criteria**                                                   |
| :-------------- | :--------- | :------------------------------------------------------------- |
| **9-10**        | Excellent  | [Specific, measurable criteria for exceptional performance]    |
| **7-8**         | Good       | [Clear expectations for above-average performance]             |
| **5-6**         | Acceptable | [Minimum standards that meet basic requirements]               |
| **3-4**         | Poor       | [Indicators of substandard performance requiring improvement]  |
| **1-2**         | Fail       | [Critical failures or complete inability to meet requirements] |

**Dependencies:**

- [Other metrics or data this metric depends on]
- [Prerequisites for accurate measurement]

---

### 3.2 Metric: [Metric Name 2]

[Repeat structure from 3.1 for each additional metric]

---

### 3.3 Metrics Summary

| **Metric Name** | **Type**                 | **Priority**      | **Target**     |
| :-------------- | :----------------------- | :---------------- | :------------- |
| [Metric 1]      | [Algorithmic/LLM/Hybrid] | [High/Medium/Low] | [Target value] |
| [Metric 2]      | [Algorithmic/LLM/Hybrid] | [High/Medium/Low] | [Target value] |

---

## 4. Evaluation Implementation

### 4.1 Evaluation Architecture

**Design Overview:**
[High-level description of the evaluation system design, including how components interact and data flows through the system]

**Evaluation Pipeline Diagram:**

```mermaid
[Mermaid diagram showing:
- Test data generation/loading
- Agent execution
- Trace collection
- Metric computation
- Results aggregation
- Report generation]
```

### 4.2 Code Structure

**Directory Layout:**

```
./                              # Repository root
├── requirements.txt            # Python dependencies (managed by uv)
├── .venv/                      # Virtual environment (created by uv)
│
└── eval/                       # Evaluation workspace
    ├── README.md               # Setup and usage instructions
    ├── eval-plan.md            # This evaluation specification
    │
    ├── metrics.py              # Metric implementations
    ├── agent_runner.py         # Agent execution wrapper [if needed]
    ├── run_evaluation.py       # Main orchestration script
    │
    ├── test-scenarios.jsonl    # Test scenarios (from /evalkit.data)
    │
    ├── traces/                 # Processed trace data
    │   └── <traceId>.json      # Individual trace files
    │
    └── results/                # Evaluation outputs
        ├── metrics.json        # Computed metric values
        ├── summary.json        # Aggregated results
        └── report.md           # Human-readable report
```

**Key Files:**

- **[`metrics.py`](eval/metrics.py):** [Description of metric implementations]
- **[`agent_runner.py`](eval/agent_runner.py):** [Description of agent execution logic]
- **[`run_evaluation.py`](eval/run_evaluation.py):** [Description of orchestration logic]

### 4.3 Technical Stack

| **Component**            | **Technology**                     | **Version/Details**     |
| :----------------------- | :--------------------------------- | :---------------------- |
| **Language**             | [e.g., Python]                     | [e.g., 3.11+]           |
| **Package Manager**      | [e.g., uv]                         | [Latest]                |
| **Tracing Framework**    | [e.g., Traceloop, OpenTelemetry]   | [Version]               |
| **OTEL Infrastructure**  | [Local collector with file export] | [Configuration details] |
| **Evaluation Framework** | [e.g., DeepEval, RAGAS, Custom]    | [Version]               |
| **LLM Gateway**          | [e.g., LiteLLM]                    | [Version]               |
| **LLM Provider**         | [e.g., AWS Bedrock, OpenAI]        | [Provider details]      |
| **LLM Model**            | [e.g., claude-sonnet-4]            | [Full model identifier] |
| **Agent Integration**    | [Direct import/API/CLI]            | [Integration method]    |
| **Results Storage**      | [JSON files/Database]              | [Storage format]        |

### 4.4 Evaluation Workflow

**Step-by-Step Process:**

1. **Setup:** [Environment preparation, dependency installation]
2. **Data Loading:** [Test scenario loading and validation]
3. **Agent Execution:** [How agent is invoked for each test case]
4. **Trace Collection:** [How traces are captured and processed]
5. **Metric Computation:** [How each metric is calculated]
6. **Results Aggregation:** [How individual results are combined]
7. **Report Generation:** [How final report is created]

**Execution Command:**

```bash
[Command to run the evaluation, e.g., python eval/run_evaluation.py]
```

---

## 5. Test Data Strategy

### 5.1 Test Scenario Design

**Scenario Coverage:**

- **[Scenario Category 1]:** [Description and purpose]
  - Number of test cases: [Count]
  - Complexity level: [Simple/Medium/Complex]
- **[Scenario Category 2]:** [Description and purpose]
  - Number of test cases: [Count]
  - Complexity level: [Simple/Medium/Complex]

**Data Generation Method:**

- [Manual curation/LLM generation/Synthetic/Real-world samples]
- [Tools or processes used]

**Test Data Location:**

- [`test-scenarios.jsonl`](eval/test-scenarios.jsonl)

### 5.2 Test Scenario Format

**Schema:**

```json
{
  "id": "[Unique identifier]",
  "category": "[Scenario category]",
  "input": "[Agent input]",
  "expected_output": "[Expected result - optional]",
  "metadata": {
    "complexity": "[Simple/Medium/Complex]",
    "tags": ["[tag1]", "[tag2]"]
  }
}
```

---

## 6. Progress Tracking

### 6.1 User Requirements Log

| **Timestamp**      | **Source**      | **Requirement**                                                      |
| :----------------- | :-------------- | :------------------------------------------------------------------- |
| [YYYY-MM-DD HH:MM] | `/evalkit.plan` | [User input from $ARGUMENTS, or "No specific requirements provided"] |

### 6.2 Design Decisions

| **Timestamp**      | **Decision**    | **Rationale**                  | **Alternatives Considered**         |
| :----------------- | :-------------- | :----------------------------- | :---------------------------------- |
| [YYYY-MM-DD HH:MM] | [Decision made] | [Why this approach was chosen] | [Other options that were evaluated] |

### 6.3 Implementation Progress

| **Timestamp**      | **Component**    | **Status**                      | **Notes**                                      |
| :----------------- | :--------------- | :------------------------------ | :--------------------------------------------- |
| [YYYY-MM-DD HH:MM] | [Component name] | [In Progress/Completed/Blocked] | [Technical details, blockers, or achievements] |

### 6.4 Issues and Resolutions

| **Timestamp**      | **Issue**             | **Resolution**        | **Impact**                  |
| :----------------- | :-------------------- | :-------------------- | :-------------------------- |
| [YYYY-MM-DD HH:MM] | [Problem encountered] | [How it was resolved] | [Effect on evaluation plan] |

---

## 7. Appendix

### 7.1 References

- [Links to relevant documentation]
- [Related evaluation frameworks or papers]
- [Agent documentation or specifications]

### 7.2 Glossary

- **[Term 1]:** [Definition]
- **[Term 2]:** [Definition]

### 7.3 Version History

| **Version** | **Date**     | **Changes**           | **Author**  |
| :---------- | :----------- | :-------------------- | :---------- |
| v3.0        | [YYYY-MM-DD] | Initial plan creation | [Name/Tool] |

---

_This evaluation plan is a living document and should be updated as the evaluation progresses and new insights are gained._
