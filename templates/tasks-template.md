---
description: "Task list template for evaluation implementation"
---

# Tasks: [AGENT NAME] Evaluation

**Input**: Design documents from `eval/`  

**Prerequisites**: plan.md (required), spec.md (required for evaluation areas)

**Focus**: Agent evaluation implementation - no unit testing required for evaluation pipelines.

**Organization**: Tasks are grouped by evaluation area to enable independent implementation and testing of each area.

## Format: `[ID] [Area] Description`
- **[Area]**: Which evaluation area this task belongs to (e.g., EA1, EA2, EA3)
- Include exact file paths in descriptions

## Path Conventions
- **Evaluation structure**: `eval/` at repository root with flat structure
- **Core files**: `eval/config.yaml`, `eval/evaluators.py`, `eval/run_evaluation.py`, `eval/test_cases.json`
- **Results**: `eval/results/` for evaluation outputs
- Paths shown below assume flat evaluation structure from plan.md

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /evalkit.tasks command MUST replace these with actual tasks based on:
  - Evaluation areas from spec.md (with their priorities P1, P2, P3...)
  - Technical requirements from plan.md
  
  Tasks MUST be organized by evaluation area so each area can be:
  - Implemented independently
  - Tested independently
  - Delivered as an evaluation increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create evaluation project structure per implementation plan
- [ ] T002 Initialize Python project with evaluation framework dependencies
- [ ] T003 Configure linting and formatting tools
- [ ] T004 Set up logging and monitoring infrastructure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY evaluation area can be implemented

**⚠️ CRITICAL**: No evaluation area work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T005 Setup agent integration and connection framework
- [ ] T006 Implement data loading and validation pipeline
- [ ] T007 Setup evaluation framework integration (DeepEval/RAGAS/Custom)
- [ ] T008 Create base evaluation classes and interfaces
- [ ] T009 Configure result storage and aggregation system
- [ ] T010 Setup configuration management system
- [ ] T011 Implement basic reporting and visualization framework

**Checkpoint**: Foundation ready - evaluation area implementation can now begin in parallel

---

## Phase 3: Evaluation Area 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this evaluation area delivers]

**Independent Test**: [How to verify this area works on its own]

### Implementation for Evaluation Area 1

- [ ] T012 [EA1] Create [Metric1] evaluator in eval/evaluators.py
- [ ] T013 [EA1] Create [Metric2] evaluator in eval/evaluators.py
- [ ] T014 [EA1] Implement [EvaluationArea1] orchestrator in eval/run_evaluation.py
- [ ] T015 [EA1] Create test scenarios for [area1] in eval/test_cases.json
- [ ] T016 [EA1] Add validation and error handling for [area1]
- [ ] T017 [EA1] Add logging and monitoring for evaluation area 1

**Checkpoint**: At this point, Evaluation Area 1 should be fully functional and testable independently

---

## Phase 4: Evaluation Area 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this evaluation area delivers]

**Independent Test**: [How to verify this area works on its own]

### Implementation for Evaluation Area 2

- [ ] T018 [EA2] Create [Metric] evaluator in eval/evaluators.py
- [ ] T019 [EA2] Implement [EvaluationArea2] orchestrator in eval/run_evaluation.py
- [ ] T020 [EA2] Create test scenarios for [area2] in eval/test_cases.json
- [ ] T021 [EA2] Integrate with Evaluation Area 1 components (if needed)

**Checkpoint**: At this point, Evaluation Areas 1 AND 2 should both work independently

---

## Phase 5: Evaluation Area 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this evaluation area delivers]

**Independent Test**: [How to verify this area works on its own]

### Implementation for Evaluation Area 3

- [ ] T022 [EA3] Create [Metric] evaluator in eval/evaluators.py
- [ ] T023 [EA3] Implement [EvaluationArea3] orchestrator in eval/run_evaluation.py
- [ ] T024 [EA3] Create test scenarios for [area3] in eval/test_cases.json

**Checkpoint**: All evaluation areas should now be independently functional

---

[Add more evaluation area phases as needed, following the same pattern]

---

## Phase N: Analysis & Reporting

**Purpose**: Results analysis and insights generation that affects multiple evaluation areas

- [ ] TXXX Implement results aggregation and statistical analysis
- [ ] TXXX Create comparative analysis between evaluation areas
- [ ] TXXX Build interactive dashboard and visualizations
- [ ] TXXX Generate comprehensive evaluation reports
- [ ] TXXX Performance optimization across all areas
- [ ] TXXX Security and data privacy validation
- [ ] TXXX Run end-to-end evaluation validation

---

## Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Project initialization and basic structure
- **Foundational (Phase 2)**: Core infrastructure - must complete before evaluation areas
- **Evaluation Areas (Phase 3+)**: Implement evaluation areas sequentially by priority (P1 → P2 → P3)
- **Analysis & Reporting (Final Phase)**: Results analysis after evaluation areas complete

### Within Each Evaluation Area

- Evaluators before orchestrators
- Test scenarios before integration
- Core implementation before cross-area integration
- Complete area before moving to next priority

---

## Implementation Strategy

### MVP First (Evaluation Area 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all areas)
3. Complete Phase 3: Evaluation Area 1
4. **STOP and VALIDATE**: Test Evaluation Area 1 independently
5. Generate report if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add Evaluation Area 1 → Test independently → Generate insights (MVP!)
3. Add Evaluation Area 2 → Test independently → Generate comparative insights
4. Add Evaluation Area 3 → Test independently → Generate comprehensive insights
5. Each area adds evaluation depth without breaking previous areas


## Notes

- [Area] label maps task to specific evaluation area for traceability
- Each evaluation area should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate area independently
- Avoid: vague tasks, cross-area dependencies that break independence
