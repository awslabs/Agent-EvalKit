---
description: Create technical implementation plans for evaluation infrastructure (tracing libraries, eval SDKs, dashboard visualization libraries, etc.)
scripts:
  sh: scripts/bash/setup-plan.sh --json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.plan` in the triggering message **is** additional context or specific planning requirements. This command creates detailed technical implementation plans for the evaluation infrastructure.

Given that context, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and PLAN_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

2. Load `templates/plan-template.md` to understand the required plan structure.

3. Load the current evaluation specification to understand the evaluation requirements.

4. Follow this execution flow:

    1. Parse user context from Input (if provided)
    2. Analyze evaluation specification for technical requirements:
       - Agent architecture and integration needs
       - Evaluation metrics and measurement requirements
       - Test data processing and management needs
       - Results storage and analysis requirements
       - Dashboard and visualization needs
    3. For unclear technical decisions:
       - Make informed choices based on evaluation requirements and common patterns
       - Only mark with [NEEDS CLARIFICATION: specific question] if:
         - The choice significantly impacts system architecture or performance
         - Multiple reasonable technology approaches exist with different trade-offs
         - No reasonable default technology stack exists for the evaluation type
       - **LIMIT: Maximum 5 [NEEDS CLARIFICATION] markers total**
       - Prioritize clarifications by impact: core architecture > integration approach > technology stack > deployment strategy
    4. Design technical architecture for evaluation infrastructure
    5. Select appropriate technology stack and frameworks
    6. Create detailed implementation plan with phases and tasks
    7. Define environment setup and dependency requirements
    8. Specify integration patterns and data flow
    9. Document configuration and deployment approach

5. **Technical Planning Process**:

   a. **Architecture Analysis**: Based on the evaluation specification:
      - Identify agent integration requirements (APIs, interfaces, data formats)
      - Determine evaluation framework needs (DeepEval, RAGAS, custom metrics)
      - Plan data pipeline architecture (ingestion, processing, storage)
      - Design results aggregation and analysis components
      - Specify monitoring and logging requirements

   b. **Technology Stack Selection**: Choose appropriate tools for:
      
      **Evaluation Frameworks**:
      - DeepEval for LLM-based agents (accuracy, relevance, faithfulness metrics)
      - RAGAS for RAG systems (context relevance, answer faithfulness)
      - Custom evaluation logic for specialized agents
      - LLM-as-a-Judge for subjective quality metrics
      
      **Data Processing**:
      - Pandas/Polars for data manipulation and analysis
      - JSON/JSONL for test case and result storage
      - SQLite/PostgreSQL for structured result storage
      - Apache Parquet for efficient data serialization
      
      **Agent Integration**:
      - HTTP clients for API-based agents
      - Direct imports for Python-based agents
      - Docker containers for isolated agent execution
      - Message queues for asynchronous processing
      
      **Monitoring & Observability**:
      - Structured logging (JSON format)
      - Execution tracing and timing
      - Error tracking and failure analysis
      - Resource usage monitoring
      
      **Visualization & Reporting**:
      - Matplotlib/Plotly for static charts
      - Plotly Dash/Streamlit for interactive dashboards
      - HTML reports with embedded visualizations
      - CSV/Excel exports for stakeholder review

   c. **Implementation Architecture**: Design the evaluation system with:
      
      ```
      eval/
      ├── results/                # Evaluation outputs
      ├── checklists/            # Task checklists and progress tracking
      ├── config.yaml            # Configuration for evaluation framework AND original agent
      ├── evaluators.py          # Evaluators
      ├── run_evaluation.py      # Main entry point with complete integration pattern
      ├── setup.sh               # Environment setup script (optional)
      ├── test_cases.json        # Test cases
      ├── spec.md                # Evaluation specification
      ├── plan.md                # Implementation plan
      └── tasks.md               # Task breakdown
      ```

   d. **Implementation Phases**: Break down the work into logical phases:
      
      **Phase 1: Foundation Setup**
      - Environment configuration and dependency installation
      - Agent integration and connectivity testing
      - Basic data loading and validation
      - Logging and monitoring infrastructure
      
      **Phase 2: Core Evaluation Engine**
      - Evaluation framework integration
      - Metrics computation implementation
      - Test case execution pipeline
      - Results storage and aggregation
      
      **Phase 3: Analysis & Reporting**
      - Results analysis and insights generation
      - Dashboard and visualization development
      - Report generation and export functionality
      - Performance optimization and scaling

   e. **Configuration Management**: Define configuration approach:
      - YAML-based configuration files for flexibility
      - Environment variable support for deployment
      - Configuration validation and error handling
      - Template configurations for common scenarios

6. **Plan Documentation**: Create comprehensive plan including:
   - Executive summary of approach and timeline
   - Detailed technical architecture diagrams
   - Technology stack rationale and alternatives considered
   - Implementation phases with tasks, dependencies, and estimates
   - Risk assessment and mitigation strategies
   - Success criteria and validation approach

7. **Quality Validation**: Ensure the plan addresses:
   - All evaluation requirements from the specification
   - Scalability and performance considerations
   - Error handling and failure recovery
   - Security and data privacy requirements
   - Maintainability and extensibility needs

8. Write the implementation plan to PLAN_FILE using the template structure.

9. **Plan Quality Validation**: After writing the initial plan, validate it against quality criteria:

   a. **Create Implementation Plan Quality Checklist**: Generate a checklist file at `EVAL_DIR/checklists/implementation_plan.md` using the checklist template structure with these validation items:
   
      ```markdown
      # Implementation Plan Quality Checklist: [AGENT NAME]
      
      **Purpose**: Validate technical implementation plan completeness and quality before proceeding to task breakdown
      **Created**: [DATE]
      **Agent**: [Link to spec.md]
      **Plan**: [Link to plan.md]
      
      ## Technical Architecture Quality
      
      - [ ] No evaluation design details (metrics, success criteria, test scenarios)
      - [ ] Focused on technical implementation and technology decisions
      - [ ] Written for development teams and technical stakeholders
      - [ ] All technology choices have clear rationale
      
      ## Implementation Completeness
      
      - [ ] No [NEEDS CLARIFICATION] markers remain
      - [ ] All major technology decisions are documented with alternatives considered
      - [ ] Architecture supports all evaluation requirements from spec
      - [ ] Implementation phases are logical and well-sequenced
      - [ ] Integration patterns and data flow are specified
      - [ ] Environment setup and dependencies are defined
      - [ ] Configuration and deployment approach is documented
      
      ## Technology Decision Quality
      
      - [ ] Evaluation framework selection is justified (DeepEval, RAGAS, custom)
      - [ ] Agent integration approach is clearly defined
      - [ ] Data storage and processing technologies are appropriate for scale
      - [ ] Visualization and reporting tools match requirements
      - [ ] Testing strategy and frameworks are specified
      - [ ] All technology choices consider maintainability and team expertise
      
      ## Notes
      
      - Items marked incomplete require plan updates before `/evalkit.tasks`
      ```
   
   b. **Run Validation Check**: Review the plan against each checklist item:
      - For each item, determine if it passes or fails
      - Document specific issues found (quote relevant plan sections)
   
   c. **Handle Validation Results**:
      
      - **If all items pass**: Mark checklist complete and proceed to step 10
      
      - **If items fail (excluding [NEEDS CLARIFICATION])**:
        1. List the failing items and specific issues
        2. Update the plan to address each issue
        3. Re-run validation until all items pass (max 3 iterations)
        4. If still failing after 3 iterations, document remaining issues in checklist notes and warn user

   d. **Handle [NEEDS CLARIFICATION] markers** (if any remain):
      1. Extract all [NEEDS CLARIFICATION: ...] markers from the plan
      2. **LIMIT CHECK**: If more than 5 markers exist, keep only the 5 most critical (by technical impact) and make informed decisions for the rest
      3. For each clarification needed (max 5), present options to user in this format:
      
         ```markdown
         ## Technical Question [N]: [Topic]
         
         **Context**: [Quote relevant plan section]
         
         **What we need to decide**: [Specific question from NEEDS CLARIFICATION marker]
         
         **Technology Options**:
         
         | Option | Technology Choice | Trade-offs & Implications |
         |--------|------------------|---------------------------|
         | A      | [First technology option] | [Performance, complexity, maintenance implications] |
         | B      | [Second technology option] | [Performance, complexity, maintenance implications] |
         | C      | [Third technology option] | [Performance, complexity, maintenance implications] |
         | Custom | Specify your preferred technology | [Explain how to provide custom choice] |
         
         **Your choice**: _[Wait for user response]_
         ```
      
      4. **CRITICAL - Table Formatting**: Ensure markdown tables are properly formatted with consistent spacing
      5. Number questions sequentially (Q1, Q2, Q3 - max 5 total)
      6. Present all questions together before waiting for responses
      7. Wait for user to respond with their choices for all questions
      8. Update the plan by replacing each [NEEDS CLARIFICATION] marker with the user's selected or provided answer
      9. Re-run validation after all clarifications are resolved

   e. **Update Checklist**: After each validation iteration, update the checklist file with current pass/fail status

10. Report completion with plan file path, architecture summary, checklist results, and readiness for the next phase (`/evalkit.tasks`).

## General Guidelines

### Planning Principles

- **Minimal Viable Implementation**: Start with essential components, add complexity incrementally
- **Framework-First**: Leverage existing evaluation frameworks before building custom solutions
- **Configuration-Driven**: Use configuration files to avoid hardcoding evaluation parameters
- **Modular Design**: Create reusable components that can be easily tested and maintained
- **Real Agent Focus**: Ensure all plans support actual agent execution, never simulation

### Technology Selection Criteria

When choosing technologies, prioritize:

1. **Evaluation Framework Alignment**: Choose tools that integrate well with DeepEval, RAGAS, or custom metrics
2. **Agent Compatibility**: Ensure selected tools can integrate with the target agent architecture
3. **Scalability**: Consider performance requirements and potential growth
4. **Maintainability**: Prefer well-documented, actively maintained libraries
5. **Team Expertise**: Consider available skills and learning curve

### For AI Generation

When creating technical plans from evaluation specifications:

1. **Make informed technology choices**: Use evaluation requirements, agent type patterns, and technical best practices to select appropriate technologies
2. **Document technology rationale**: Record reasoning for each major technology decision in the alternatives table
3. **Limit clarifications**: Maximum 5 [NEEDS CLARIFICATION] markers - use only for critical technical decisions that:
   - Significantly impact system architecture, performance, or maintainability
   - Have multiple reasonable technology approaches with different trade-offs
   - Lack any reasonable default technology stack for the evaluation type
4. **Prioritize clarifications**: core architecture > integration approach > technology stack > deployment strategy
5. **Think like a technical architect**: Every technology choice should have clear rationale and trade-off analysis

**Examples of reasonable defaults** (don't ask about these):

- **Evaluation frameworks**: DeepEval for LLM agents, RAGAS for RAG systems, pytest for testing
- **Data processing**: Pandas for data manipulation, JSON for simple storage, SQLite for structured queries
- **Agent integration**: HTTP API calls for web services, direct imports for Python agents
- **Visualization**: Matplotlib for static reports, Streamlit for interactive dashboards
- **Configuration**: YAML files for flexibility, environment variables for deployment

**Common areas needing clarification** (only if no reasonable default exists):

- **Architecture approach**: When multiple valid patterns exist (microservices vs monolithic, sync vs async)
- **Storage strategy**: When evaluation scale or data complexity requirements are unclear
- **Integration method**: When agent architecture supports multiple integration approaches
- **Deployment target**: When production requirements vs local development needs are unclear

### Architecture Patterns

**Recommended Patterns**:
- **Pipeline Architecture**: Linear flow from test cases → execution → evaluation → reporting
- **Configuration-Driven**: Externalize all parameters and settings
- **Modular Components**: Separate concerns (data, execution, evaluation, reporting)
- **Error Boundaries**: Isolate failures to prevent cascade effects
- **Observability-First**: Built-in logging, metrics, and tracing

**Anti-Patterns to Avoid**:
- **Monolithic Design**: Single large script handling all concerns
- **Hardcoded Values**: Embedding configuration in code
- **Agent Simulation**: Mocking or faking agent responses
- **Framework Lock-in**: Tight coupling to specific evaluation tools
- **Silent Failures**: Poor error handling and reporting

