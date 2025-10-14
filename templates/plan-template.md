# Evaluation Implementation Plan: [AGENT NAME]

**Branch**: `[###-agent-evaluation]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Agent evaluation specification from `/specs/[###-agent-evaluation]/spec.md`

**Note**: This template is filled in by the `/evalkit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from evaluation spec: primary evaluation objectives + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the evaluation project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Node.js 18+ or NEEDS CLARIFICATION]  
**Evaluation Framework**: [e.g., DeepEval, RAGAS, Custom or NEEDS CLARIFICATION]  
**Agent Integration**: [e.g., Direct import, HTTP API, Docker container or NEEDS CLARIFICATION]  
**Data Storage**: [e.g., JSON files, SQLite, PostgreSQL or NEEDS CLARIFICATION]  
**Visualization**: [e.g., Matplotlib, Plotly, Streamlit dashboard or NEEDS CLARIFICATION]  
**Testing Framework**: [e.g., pytest, unittest, custom or NEEDS CLARIFICATION]  
**Target Environment**: [e.g., Local development, Cloud deployment, CI/CD or NEEDS CLARIFICATION]
**Evaluation Type**: [accuracy/performance/robustness - determines metrics focus]  
**Performance Goals**: [evaluation-specific, e.g., 100 test cases/min, <5s per evaluation, 95% accuracy or NEEDS CLARIFICATION]  
**Constraints**: [evaluation-specific, e.g., <1GB memory, real-time processing, no simulation or NEEDS CLARIFICATION]  
**Scale/Scope**: [evaluation-specific, e.g., 1000 test cases, 5 evaluation metrics, 3 agent variants or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this evaluation)

```
specs/[###-agent-evaluation]/
├── plan.md              # This file (/evalkit.plan command output)
├── research.md          # Phase 0 output (/evalkit.plan command)
├── evaluation-design.md # Phase 1 output (/evalkit.plan command)
├── metrics-spec.md      # Phase 1 output (/evalkit.plan command)
├── test-scenarios/      # Phase 1 output (/evalkit.plan command)
└── tasks.md             # Phase 2 output (/evalkit.tasks command - NOT created by /evalkit.plan)
```

### Evaluation Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this evaluation. Delete unused options and expand the chosen structure with
  real paths (e.g., eval/agents, eval/metrics). The delivered plan must
  not include Option labels.
-->

```
# [REMOVE IF UNUSED] Option 1: Simple evaluation (DEFAULT)
eval/
├── config/
│   ├── evaluation.yaml
│   ├── agent.yaml
│   └── metrics.yaml
├── data/
│   ├── test_cases.jsonl
│   ├── expected_outputs/
│   └── results/
├── src/
│   ├── evaluators/
│   ├── agents/
│   ├── data/
│   └── reporting/
└── scripts/
    ├── run_evaluation.py
    ├── generate_report.py
    └── setup_env.sh

# [REMOVE IF UNUSED] Option 2: Multi-agent evaluation (when multiple agents detected)
eval/
├── config/
│   ├── evaluation.yaml
│   └── agents/
│       ├── agent1.yaml
│       ├── agent2.yaml
│       └── agent3.yaml
├── data/
│   ├── shared/
│   │   └── test_cases.jsonl
│   └── results/
│       ├── agent1/
│       ├── agent2/
│       └── comparative/
└── src/
    ├── evaluators/
    ├── agents/
    ├── comparative/
    └── reporting/

# [REMOVE IF UNUSED] Option 3: Production evaluation system (when "production" + "monitoring" detected)
eval/
├── config/
├── data/
├── src/
├── monitoring/
│   ├── dashboards/
│   ├── alerts/
│   └── metrics/
├── deployment/
│   ├── docker/
│   ├── k8s/
│   └── ci-cd/
└── docs/
    ├── setup.md
    ├── usage.md
    └── troubleshooting.md
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., Custom evaluation framework] | [specific need] | [why DeepEval/RAGAS insufficient] |
| [e.g., Multiple storage systems] | [specific problem] | [why single storage insufficient] |
