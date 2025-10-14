---
description: "Task list template for evaluation implementation"
---

# Tasks: [AGENT NAME] Evaluation

**Input**: Design documents from `/specs/[###-agent-evaluation]/`
**Prerequisites**: plan.md (required), spec.md (required for evaluation areas), research.md, evaluation-design.md, metrics-spec.md

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the evaluation specification.

**Organization**: Tasks are grouped by evaluation area to enable independent implementation and testing of each area.

## Format: `[ID] [P?] [Area] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Area]**: Which evaluation area this task belongs to (e.g., EA1, EA2, EA3)
- Include exact file paths in descriptions

## Path Conventions
- **Simple evaluation**: `eval/`, `eval/tests/` at repository root
- **Multi-agent**: `eval/agents/`, `eval/comparative/`
- **Production**: `eval/src/`, `eval/monitoring/`, `eval/deployment/`
- Paths shown below assume simple evaluation - adjust based on plan.md structure

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /evalkit.tasks command MUST replace these with actual tasks based on:
  - Evaluation areas from spec.md (with their priorities P1, P2, P3...)
  - Technical requirements from plan.md
  - Metrics from evaluation-design.md
  - Test scenarios from test-scenarios/
  
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
- [ ] T003 [P] Configure linting and formatting tools
- [ ] T004 [P] Set up logging and monitoring infrastructure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY evaluation area can be implemented

**⚠️ CRITICAL**: No evaluation area work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T005 Setup agent integration and connection framework
- [ ] T006 [P] Implement data loading and validation pipeline
- [ ] T007 [P] Setup evaluation framework integration (DeepEval/RAGAS/Custom)
- [ ] T008 Create base evaluation classes and interfaces
- [ ] T009 Configure result storage and aggregation system
- [ ] T010 Setup configuration management system
- [ ] T011 [P] Implement basic reporting and visualization framework

**Checkpoint**: Foundation ready - evaluation area implementation can now begin in parallel

---

## Phase 3: Evaluation Area 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this evaluation area delivers]

**Independent Test**: [How to verify this area works on its own]

### Tests for Evaluation Area 1 (OPTIONAL - only if tests requested) ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [EA1] Unit test for [metric] in eval/tests/unit/test_[metric].py
- [ ] T013 [P] [EA1] Integration test for [evaluation flow] in eval/tests/integration/test_[area].py

### Implementation for Evaluation Area 1

- [ ] T014 [P] [EA1] Create [Metric1] evaluator in eval/src/evaluators/[metric1].py
- [ ] T015 [P] [EA1] Create [Metric2] evaluator in eval/src/evaluators/[metric2].py
- [ ] T016 [EA1] Implement [EvaluationArea1] orchestrator in eval/src/evaluators/[area1].py (depends on T014, T015)
- [ ] T017 [EA1] Create test scenarios for [area1] in eval/data/test_cases/[area1].jsonl
- [ ] T018 [EA1] Add validation and error handling for [area1]
- [ ] T019 [EA1] Add logging and monitoring for evaluation area 1

**Checkpoint**: At this point, Evaluation Area 1 should be fully functional and testable independently

---

## Phase 4: Evaluation Area 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this evaluation area delivers]

**Independent Test**: [How to verify this area works on its own]

### Tests for Evaluation Area 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [EA2] Unit test for [metric] in eval/tests/unit/test_[metric].py
- [ ] T021 [P] [EA2] Integration test for [evaluation flow] in eval/tests/integration/test_[area].py

### Implementation for Evaluation Area 2

- [ ] T022 [P] [EA2] Create [Metric] evaluator in eval/src/evaluators/[metric].py
- [ ] T023 [EA2] Implement [EvaluationArea2] orchestrator in eval/src/evaluators/[area2].py
- [ ] T024 [EA2] Create test scenarios for [area2] in eval/data/test_cases/[area2].jsonl
- [ ] T025 [EA2] Integrate with Evaluation Area 1 components (if needed)

**Checkpoint**: At this point, Evaluation Areas 1 AND 2 should both work independently

---

## Phase 5: Evaluation Area 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this evaluation area delivers]

**Independent Test**: [How to verify this area works on its own]

### Tests for Evaluation Area 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [EA3] Unit test for [metric] in eval/tests/unit/test_[metric].py
- [ ] T027 [P] [EA3] Integration test for [evaluation flow] in eval/tests/integration/test_[area].py

### Implementation for Evaluation Area 3

- [ ] T028 [P] [EA3] Create [Metric] evaluator in eval/src/evaluators/[metric].py
- [ ] T029 [EA3] Implement [EvaluationArea3] orchestrator in eval/src/evaluators/[area3].py
- [ ] T030 [EA3] Create test scenarios for [area3] in eval/data/test_cases/[area3].jsonl

**Checkpoint**: All evaluation areas should now be independently functional

---

[Add more evaluation area phases as needed, following the same pattern]

---

## Phase N: Analysis & Reporting

**Purpose**: Results analysis and insights generation that affects multiple evaluation areas

- [ ] TXXX [P] Implement results aggregation and statistical analysis
- [ ] TXXX [P] Create comparative analysis between evaluation areas
- [ ] TXXX Build interactive dashboard and visualizations
- [ ] TXXX [P] Generate comprehensive evaluation reports
- [ ] TXXX Performance optimization across all areas
- [ ] TXXX [P] Additional unit tests (if requested) in eval/tests/unit/
- [ ] TXXX Security and data privacy validation
- [ ] TXXX Run end-to-end evaluation validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all evaluation areas
- **Evaluation Areas (Phase 3+)**: All depend on Foundational phase completion
  - Evaluation areas can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Analysis & Reporting (Final Phase)**: Depends on all desired evaluation areas being complete

### Evaluation Area Dependencies

- **Evaluation Area 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other areas
- **Evaluation Area 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with EA1 but should be independently testable
- **Evaluation Area 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with EA1/EA2 but should be independently testable

### Within Each Evaluation Area

- Tests (if included) MUST be written and FAIL before implementation
- Evaluators before orchestrators
- Test scenarios before integration
- Core implementation before cross-area integration
- Area complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all evaluation areas can start in parallel (if team capacity allows)
- All tests for an evaluation area marked [P] can run in parallel
- Evaluators within an area marked [P] can run in parallel
- Different evaluation areas can be worked on in parallel by different team members

---

## Parallel Example: Evaluation Area 1

```bash
# Launch all tests for Evaluation Area 1 together (if tests requested):
Task: "Unit test for [metric] in eval/tests/unit/test_[metric].py"
Task: "Integration test for [evaluation flow] in eval/tests/integration/test_[area].py"

# Launch all evaluators for Evaluation Area 1 together:
Task: "Create [Metric1] evaluator in eval/src/evaluators/[metric1].py"
Task: "Create [Metric2] evaluator in eval/src/evaluators/[metric2].py"
```

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

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: Evaluation Area 1
   - Developer B: Evaluation Area 2
   - Developer C: Evaluation Area 3
3. Areas complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Area] label maps task to specific evaluation area for traceability
- Each evaluation area should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate area independently
- Avoid: vague tasks, same file conflicts, cross-area dependencies that break independence
