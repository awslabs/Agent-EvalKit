---
description: Generate actionable task lists for evaluation implementation
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.tasks` in the triggering message **is** additional context or specific task generation requirements. This command generates detailed, actionable task lists for implementing the evaluation infrastructure.

Given that context, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and TASKS_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

2. Load `templates/tasks-template.md` to understand the required task structure.

3. Load the current evaluation specification and implementation plan to understand requirements.

4. Follow this execution flow:

    1. Parse user context from Input (if provided)
    2. Analyze implementation plan for technical components and phases
    3. Break down each phase into specific, actionable tasks
    4. Define task dependencies, priorities, and acceptance criteria
    5. Estimate effort and identify required skills for each task
    6. Create task sequences that enable parallel work where possible
    7. Generate comprehensive task list with clear ownership and timelines

5. **Task Generation Process**:

   a. **Phase Analysis**: For each implementation phase identified in the plan:
      - Extract major deliverables and milestones
      - Identify technical components and dependencies
      - Determine required skills and expertise areas
      - Assess complexity and effort requirements

   b. **Task Breakdown Structure**: Create hierarchical task breakdown:
      
      **Phase 1: Foundation Setup**
      ```
      1.1 Environment Configuration
          1.1.1 Set up Python virtual environment with uv
          1.1.2 Install core dependencies (evaluation frameworks)
          1.1.3 Configure development tools (linting, testing)
          1.1.4 Set up logging and monitoring infrastructure
      
      1.2 Agent Integration
          1.2.1 Analyze agent interface and connection requirements
          1.2.2 Implement agent connector/wrapper
          1.2.3 Create agent health check and validation
          1.2.4 Test basic agent connectivity and response
      
      1.3 Data Infrastructure
          1.3.1 Design test case data schema
          1.3.2 Implement data loading and validation
          1.3.3 Create result storage structure
          1.3.4 Set up configuration management system
      ```

   c. **Task Specification Format**: For each task, provide:
      
      ```markdown
      ### Task [ID]: [Task Name]
      
      **Phase**: [Phase Number and Name]
      **Priority**: [High/Medium/Low]
      **Estimated Effort**: [Hours/Days]
      **Skills Required**: [Technical skills needed]
      **Dependencies**: [Other tasks that must complete first]
      
      **Description**:
      [Clear description of what needs to be accomplished]
      
      **Acceptance Criteria**:
      - [ ] [Specific, testable criterion 1]
      - [ ] [Specific, testable criterion 2]
      - [ ] [Specific, testable criterion 3]
      
      **Implementation Notes**:
      - [Technical guidance or considerations]
      - [Recommended approaches or tools]
      - [Potential challenges and solutions]
      
      **Validation Steps**:
      1. [How to verify the task is complete]
      2. [Testing or validation procedures]
      3. [Quality checks to perform]
      ```

   d. **Task Categories and Examples**:

      **Environment & Setup Tasks**:
      - Virtual environment creation and dependency management
      - Configuration file setup and validation
      - Development tool configuration (IDE, linting, testing)
      - Documentation structure and templates

      **Agent Integration Tasks**:
      - Agent interface analysis and documentation
      - Connection wrapper/adapter implementation
      - Authentication and security setup
      - Error handling and retry logic

      **Data Management Tasks**:
      - Test case schema design and validation
      - Data loading and preprocessing pipelines
      - Result storage and retrieval systems
      - Data quality checks and validation

      **Evaluation Engine Tasks**:
      - Evaluation framework integration (DeepEval/RAGAS)
      - Custom metric implementation
      - Batch processing and parallel execution
      - Progress tracking and monitoring

      **Analysis & Reporting Tasks**:
      - Results aggregation and statistical analysis
      - Visualization and dashboard development
      - Report generation and export functionality
      - Performance analysis and optimization

      **Testing & Validation Tasks**:
      - Unit tests for core components
      - Integration tests for end-to-end workflows
      - Performance testing and benchmarking
      - User acceptance testing and documentation

   e. **Task Dependencies and Sequencing**: Define clear dependency chains:
      - **Sequential Dependencies**: Tasks that must complete before others can start
      - **Parallel Opportunities**: Tasks that can be worked on simultaneously
      - **Critical Path**: Sequence of tasks that determines minimum project duration
      - **Risk Mitigation**: Alternative approaches if dependencies are blocked

   f. **Effort Estimation Guidelines**:
      
      **Simple Tasks** (2-4 hours):
      - Configuration file creation
      - Basic data loading scripts
      - Simple metric implementations
      - Documentation updates
      
      **Medium Tasks** (1-2 days):
      - Agent integration and testing
      - Evaluation framework setup
      - Dashboard component development
      - Comprehensive testing suites
      
      **Complex Tasks** (3-5 days):
      - Custom evaluation framework development
      - Advanced analytics and reporting
      - Performance optimization
      - Production deployment setup

6. **Task List Organization**: Structure the task list for maximum usability:
   - Group tasks by phase and functional area
   - Clearly mark dependencies and prerequisites
   - Include effort estimates and skill requirements
   - Provide clear acceptance criteria for each task
   - Add implementation guidance and best practices

7. **Quality Assurance**: Ensure task list completeness:
   - All plan components are covered by tasks
   - Tasks are specific and actionable
   - Acceptance criteria are measurable
   - Dependencies are clearly defined
   - Effort estimates are realistic

8. Write the task list to TASKS_FILE using the template structure.

9. Report completion with task file path, summary of task breakdown, and readiness for the next phase (`/evalkit.implement`).

## General Guidelines

### Task Quality Standards

**Good Tasks**:
- Have clear, specific objectives
- Include measurable acceptance criteria
- Specify required skills and tools
- Provide implementation guidance
- Can be completed by a single person
- Have realistic effort estimates

**Poor Tasks**:
- Are vague or open-ended
- Lack clear completion criteria
- Don't specify dependencies
- Are too large or complex
- Require multiple skill sets
- Have unrealistic timelines

### Task Sizing Principles

**Right-Sized Tasks**:
- Can be completed in 0.5-3 days
- Have single, clear objectives
- Can be validated independently
- Don't require multiple people
- Have minimal external dependencies

**Task Splitting Indicators**:
- Task takes more than 3 days
- Has multiple distinct objectives
- Requires different skill sets
- Has complex dependency chains
- Cannot be easily validated

### Dependency Management

**Types of Dependencies**:
- **Technical**: One task's output is needed as input for another
- **Resource**: Same person/tool needed for multiple tasks
- **Knowledge**: Learning from one task informs another
- **Sequential**: Logical order of implementation
- **External**: Dependencies on external systems or approvals

**Dependency Documentation**:
- Clearly identify what is needed from prerequisite tasks
- Specify the exact deliverables or outcomes required
- Note any partial dependencies (task can start but not complete)
- Identify critical path dependencies that could delay the project

### Parallel Work Opportunities

Identify tasks that can be worked on simultaneously:
- **Independent Components**: Different parts of the system
- **Different Skill Sets**: Frontend vs backend vs data tasks
- **Preparation Work**: Documentation, setup, research tasks
- **Testing Tasks**: Can often run parallel to development

### Risk Mitigation in Task Planning

**Common Risks and Mitigation Tasks**:
- **Agent Integration Issues**: Include early connectivity testing tasks
- **Framework Compatibility**: Add proof-of-concept validation tasks
- **Performance Problems**: Include performance testing in each phase
- **Data Quality Issues**: Add data validation and cleaning tasks
- **Scope Creep**: Include regular review and validation checkpoints
