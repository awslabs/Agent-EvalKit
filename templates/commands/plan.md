---
description: Create technical implementation plans for evaluation infrastructure (tracing libraries, eval SDKs, dashboard visualization libraries, agent simulation libraries, etc.)
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
    3. Design technical architecture for evaluation infrastructure
    4. Select appropriate technology stack and frameworks
    5. Create detailed implementation plan with phases and tasks
    6. Define environment setup and dependency requirements
    7. Specify integration patterns and data flow
    8. Document configuration and deployment approach

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
      - Streamlit/Gradio for interactive dashboards
      - HTML reports with embedded visualizations
      - CSV/Excel exports for stakeholder review

   c. **Implementation Architecture**: Design the evaluation system with:
      
      ```
      evaluation/
      ├── config/
      │   ├── evaluation.yaml      # Evaluation configuration
      │   ├── agent.yaml          # Agent connection settings
      │   └── metrics.yaml        # Metrics and thresholds
      ├── data/
      │   ├── test_cases.jsonl    # Test scenarios
      │   ├── expected_outputs/   # Ground truth data
      │   └── results/           # Evaluation results
      ├── src/
      │   ├── evaluators/        # Metric computation
      │   ├── agents/           # Agent integration
      │   ├── data/             # Data processing
      │   └── reporting/        # Results analysis
      ├── scripts/
      │   ├── run_evaluation.py  # Main execution script
      │   ├── generate_report.py # Report generation
      │   └── setup_env.sh      # Environment setup
      └── requirements.txt       # Python dependencies
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
      
      **Phase 4: Validation & Deployment**
      - End-to-end testing and validation
      - Documentation and user guides
      - Deployment automation and CI/CD
      - Monitoring and alerting setup

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

9. Report completion with plan file path, architecture summary, and readiness for the next phase (`/evalkit.tasks`).

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

### Implementation Estimates

Provide realistic time estimates based on:
- **Simple Agent Evaluation**: 1-2 weeks (basic metrics, small test set)
- **Comprehensive Evaluation**: 3-4 weeks (multiple metrics, large test set, dashboard)
- **Complex Multi-Agent**: 4-6 weeks (multiple agents, comparative analysis, advanced reporting)
- **Production-Ready System**: 6-8 weeks (full automation, monitoring, deployment)

Include buffer time for:
- Agent integration challenges (20-30% additional time)
- Custom metric development (varies widely)
- Dashboard and visualization polish (15-25% additional time)
- Testing and validation (20-30% additional time)
