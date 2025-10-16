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
    5. Generate comprehensive task list for AI assistant implementation

5. **Task Generation Process**:

   a. **Phase Analysis**: For each implementation phase identified in the plan:
      - Extract major deliverables and milestones
      - Identify technical components and dependencies
      - Assess implementation complexity and requirements

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
      - [File paths and specific implementation details]
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
      - End-to-end evaluation workflow testing
      - Performance testing and benchmarking
      - Validation of evaluation results and metrics

   e. **Task Dependencies and Sequencing**: Define clear dependency chains:
      - **Sequential Dependencies**: Tasks that must complete before others can start
      - **Implementation Order**: Logical sequence for AI assistant to follow
      - **Foundation First**: Core infrastructure before evaluation areas

6. **Task List Organization**: Structure the task list for AI assistant implementation:
   - Group tasks by phase and functional area
   - Clearly mark dependencies and prerequisites
   - Provide clear acceptance criteria for each task
   - Add implementation guidance and file paths

7. **Quality Assurance**: Ensure task list completeness:
   - All plan components are covered by tasks
   - Tasks are specific and actionable
   - Acceptance criteria are measurable
   - Dependencies are clearly defined
   - File paths and implementation details are specified

8. Write the task list to TASKS_FILE using the template structure.

9. Report completion with task file path, summary of task breakdown, and readiness for the next phase (`/evalkit.implement`).

## General Guidelines

### Task Quality Standards

**Good Tasks**:
- Have clear, specific objectives
- Include measurable acceptance criteria
- Specify exact file paths and implementation details
- Provide technical guidance for AI assistants
- Can be completed independently
- Have clear validation steps

**Poor Tasks**:
- Are vague or open-ended
- Lack clear completion criteria
- Don't specify dependencies
- Don't include file paths or technical details
- Have unclear validation criteria

### Task Sizing Principles

**Right-Sized Tasks**:
- Have single, clear objectives
- Can be validated independently
- Focus on specific files or components
- Have minimal external dependencies

**Task Splitting Indicators**:
- Has multiple distinct objectives
- Spans multiple files or components
- Has complex dependency chains
- Cannot be easily validated

### Dependency Management

**Types of Dependencies**:
- **Technical**: One task's output is needed as input for another
- **Sequential**: Logical order of implementation
- **Foundation**: Core infrastructure must complete before evaluation areas

**Dependency Documentation**:
- Clearly identify what is needed from prerequisite tasks
- Specify the exact deliverables or file outputs required
- Note which files or components must exist before starting

### Implementation Approach for AI Assistants

**Sequential Implementation**:
- AI assistants work through tasks one at a time
- Each task builds on previous completed work
- Clear file paths and technical specifications guide implementation
- Validation steps ensure quality before proceeding to next task

**Task Validation**:
- **File Creation**: Verify required files are created with correct structure
- **Functionality Testing**: Test that implemented features work as expected
- **Integration Validation**: Ensure new components integrate with existing code
- **Quality Checks**: Validate code follows best practices and requirements
