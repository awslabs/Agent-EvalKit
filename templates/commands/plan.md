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

   b. **Technology Stack Selection**: Choose appropriate tools based on evaluation requirements and agent architecture. Focus on proven, well-documented solutions that integrate well with the target agent.

   c. **Implementation Architecture**: Design the evaluation system with:
      
      ```
      eval/
      ├── results/                # Evaluation outputs
      ├── config.yaml            # Configuration for evaluation framework AND original agent
      ├── evaluators.py          # Evaluators
      ├── run_evaluation.py      # Main entry point with complete integration pattern
      ├── test_cases.json        # Test cases
      ├── spec.md                # Evaluation specification
      └── plan.md                # Implementation plan with integrated tasks
      ```

   d. **Implementation Approach**: Streamlined task-based implementation:
      
      **Setup Project Structure**
      - Create evaluation project structure based on file structure
      
      **Core Evaluation Logic**
      - Implement all evaluation area evaluators
      - Create test scenarios and orchestration
      - Add configuration management
      
      **Results & Analysis**
      - Implement results aggregation and visualization
      
      **Code Review & Environment Setup**
      - Conduct code review and fix critical issues
      - Set up Python environment with dependencies

   e. **Configuration Management**: Define configuration approach:
      - YAML-based configuration files for flexibility
      - Environment variable support for deployment
      - Configuration validation and error handling
      - Template configurations for common scenarios

6. **Plan Documentation**: Create streamlined plan including:
   - Technical stack selection with rationale
   - Core architecture approach
   - Implementation tasks optimized for AI-first development
   - File structure and execution strategy
   - Focus on core evaluation logic, avoid over-engineering

7. Write the implementation plan to PLAN_FILE using the template structure.

8. **Handle [NEEDS CLARIFICATION] markers** (if any remain):

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
   8. Update the plan by replacing each [NEEDS CLARIFICATION] marker with the user's answer
   9. If no clarifications needed, proceed directly to step 10

9. Report completion with plan file path, technical summary, and readiness for implementation. The plan now includes integrated tasks, eliminating the need for a separate `/evalkit.tasks` command.

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

### Architecture Principles

**Key Principles**:
- **Simple Structure**: Use the flat `eval/` directory structure
- **Configuration-Driven**: Externalize parameters in `config.yaml`
- **Real Agent Focus**: Always use actual agent execution, never simulation
- **Focused Implementation**: Avoid over-engineering, focus on core evaluation logic

