# Agent Evaluation Implementation Plan: [AGENT NAME]

**Branch**: `[###-eval-pipeline]` | **Date**: [DATE]  
**Agent Path**: [Path to agent code/repository]  
**Spec**: `eval/spec.md`  
**User Query**: "$ARGUMENTS" *(planning context if provided)*  
**Plan Path**: `eval/plan.md`

**Note**: This template is filled in by the `/evalkit.plan` command. See `.evalkit/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from evaluation spec: primary evaluation objectives]

## Technical Stack

**Language/Version**: [e.g., Python 3.11, Node.js 18+ or NEEDS CLARIFICATION]  
**Evaluation Libraries**: [e.g., DeepEval, Langfuse, RAGAS, Custom or NEEDS CLARIFICATION]  
**Agent Integration**: [e.g., Direct import, Wrapper, HTTP API, Docker container or NEEDS CLARIFICATION]  
**Data Storage**: [e.g., JSON files, SQLite, PostgreSQL or NEEDS CLARIFICATION]  
**Visualization**: [e.g., Plotly Dash, Streamlit dashboard or NEEDS CLARIFICATION]  

## Core Architecture

**Evaluation Pipeline**: [e.g., Sequential processing vs parallel execution - approach and rationale]
**Configuration**: [e.g., YAML files for flexibility - configuration approach]
**Error Handling**: [e.g., Graceful degradation vs fail-fast - error strategy]
**Results Storage**: [e.g., JSON files for simplicity vs SQLite for queries - storage approach]

## File Structure

```
eval/
├── config.yaml              # Evaluation configuration
├── evaluators.py            # All evaluation logic
├── run_evaluation.py        # Main execution script
├── test_cases.json          # Test scenarios
├── results/                 # Evaluation outputs
├── spec.md                  # Evaluation specification
└── plan.md                  # This implementation plan
```

## Implementation Tasks

### Setup Project Structure
- [ ] Create evaluation project structure based on the decided file structure

### Core Evaluation Logic
- [ ] Implement all evaluation area evaluators in `eval/evaluators.py`
- [ ] Create test scenarios in `eval/test_cases.json`
- [ ] Build main evaluation orchestration in `eval/run_evaluation.py`
- [ ] Add configuration management in `eval/config.yaml`

### Results & Analysis
- [ ] Implement results aggregation and analysis
- [ ] Create visualization and reporting

### Code Review & Environment Setup
- [ ] Conduct a code review to identify critical issues and fix
- [ ] Set up Python environment with dependencies (using uv by default)

## Important Notes

- Focus on core evaluation logic, avoid over-engineering
- Each evaluation area should be testable independently within the unified implementation
- All evaluation uses actual agent execution, no simulation