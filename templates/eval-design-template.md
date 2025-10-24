# Agent Evaluation Specification: [AGENT NAME]

**Branch**: `[###-eval-pipeline]` | **Date**: [DATE]  
**Agent Path**: [Path to agent code/repository]  
**Trace Path**: [Path to execution trace] *(if already provided)*
**User Query**: "$ARGUMENTS" *(designing context if provided)*
**Design Path**: [Path to evaluation design document]

**Note**: This template is filled in by the `/evalkit.design` command. See `.evalkit/templates/commands/design.md` for the execution workflow.

## Agent Analysis & Overview *(mandatory)*

<!--
  IMPORTANT: Agent analysis should be PRIORITIZED as evaluation areas ordered by importance.
  Each evaluation area must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable evaluation that delivers meaningful insights.
  
  Assign priorities (P1, P2, P3, etc.) to each area, where P1 is the most critical.
  Think of each area as a standalone slice of evaluation that can be:
  - Evaluated independently
  - Tested independently
  - Reported independently
  - Demonstrated to stakeholders independently
-->

### Agent Architecture & Capabilities

**Agent Type**: [e.g., Conversational, RAG, Tool-using, Code generation]  
**Input/Output Formats**: [Describe data types and interaction patterns]  
**Key Functions**: [List primary capabilities and decision points]  
**Available Tools**: [If applicable, list tools the agent can use]  
**Technology Stack**: [Languages, frameworks, dependencies] 

**Agent Workflow Diagram**:
```mermaid
flowchart TD
    A[User Input] --> B[Agent Processing]
    B --> C[Decision Point]
    C --> D[Tool Usage/Action]
    D --> E[Response Generation]
    E --> F[User Output]
    
    %% Add specific nodes for your agent:
    %% Example: C --> G[RAG Retrieval]
    %% Example: C --> H[Code Generation]
    %% Example: G --> I[Context Processing]
```

*Note: Replace the generic workflow above with your agent's specific flow, showing key decision points, tool usage, and data transformations.*

### Evaluation Area 1 - [Brief Title] (Priority: P1)

[Describe this evaluation focus in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be evaluated independently - e.g., "Can be fully tested by [specific scenarios] and delivers [specific insights]"]

**Metrics**:

1. **Metric**: [specific measurement] 
2. **Metric**: [specific measurement]

---

### Evaluation Area 2 - [Brief Title] (Priority: P2)

[Describe this evaluation focus in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be evaluated independently]

**Metrics**:

1. **Metric**: [specific measurement]
2. **Metric**: [specific measurement]

---

[Add more evaluation areas as needed, each with an assigned priority]

### Edge Cases & Failure Modes

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases for agent evaluation.
-->

- What happens when [agent receives ambiguous input]?
- How does agent handle [out-of-scope requests]?
- What occurs during [API failures or timeouts]?

## Evaluation Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right evaluation requirements.
-->

### Functional Requirements

- **ER-001**: Evaluation MUST [specific capability, e.g., "measure response accuracy on test scenarios"]
- **ER-002**: Evaluation MUST [specific capability, e.g., "track execution time for all queries"]  
- **ER-003**: System MUST be able to [key measurement, e.g., "detect tool usage patterns"]
- **ER-004**: Evaluation MUST [data requirement, e.g., "store results for comparative analysis"]
- **ER-005**: System MUST [behavior, e.g., "log all agent interactions and responses"]

*Example of marking unclear requirements:*

- **ER-006**: Evaluation MUST measure quality via [NEEDS CLARIFICATION: quality metric not specified - accuracy, relevance, faithfulness?]
- **ER-007**: System MUST retain evaluation data for [NEEDS CLARIFICATION: retention period not specified]

### Key Test Scenarios *(include if evaluation involves specific test cases)*

- **[Scenario Type 1]**: [What it tests, key characteristics without implementation]
- **[Scenario Type 2]**: [What it tests, relationships to other scenarios]

## Implementation Plan *(mandatory)*

<!--
  This section defines the technical implementation approach for the evaluation infrastructure.
  Focus on practical decisions that enable trace-based evaluation of the agent.
-->

### Technical Stack

**Language/Version**: [e.g., Python 3.11, Node.js 18+ or NEEDS CLARIFICATION]
**Evaluation Libraries**: [e.g., DeepEval, Langfuse, RAGAS, Custom or NEEDS CLARIFICATION]
**Agent Integration**: [e.g., Direct import, Wrapper, HTTP API, Docker container or NEEDS CLARIFICATION]
**Data Storage**: [e.g., JSON files, SQLite, PostgreSQL or NEEDS CLARIFICATION]
**Visualization**: [e.g., Plotly Dash, Streamlit dashboard or NEEDS CLARIFICATION]

### Core Architecture

**Evaluation Pipeline**: [e.g., Sequential processing vs parallel execution - approach and rationale]
**Configuration**: [e.g., YAML files for flexibility - configuration approach]
**Error Handling**: [e.g., Graceful degradation vs fail-fast - error strategy]
**Results Storage**: [e.g., JSON files for simplicity vs SQLite for queries - storage approach]

### File Structure

```
eval/
├── config.yaml              # Evaluation configuration
├── evaluators.py            # All evaluation logic
├── run_evaluation.py        # Main execution script
├── test_cases.json          # Test scenarios
├── results/                 # Evaluation outputs
└── eval-design.md           # This evaluation specification and plan
```

### Implementation Tasks

#### Setup Project Structure
- [ ] Create evaluation project structure based on the decided file structure

#### Core Evaluation Logic
- [ ] Implement all evaluation area evaluators in `eval/evaluators.py`
- [ ] Create test scenarios in `eval/test_cases.json`
- [ ] Build main evaluation orchestration in `eval/run_evaluation.py`
- [ ] Add configuration management in `eval/config.yaml`

#### Results & Analysis
- [ ] Implement results aggregation and analysis
- [ ] Create visualization and reporting

#### Code Review & Environment Setup
- [ ] Conduct a code review to identify critical issues and fix
- [ ] Set up Python environment with dependencies (using uv by default)

### Important Notes

- Focus on core evaluation logic, avoid over-engineering
- Each evaluation area should be testable independently within the unified implementation
- All evaluation uses actual agent execution, no simulation

