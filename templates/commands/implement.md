---
description: Execute all tasks to build the evaluation pipeline according to the plan
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.implement` in the triggering message **is** additional context or specific implementation requirements. This command executes the implementation tasks to build the evaluation pipeline according to the plan.

Given that context, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and IMPLEMENTATION_STATUS. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

2. Load the current task list and implementation plan to understand what needs to be built.

3. Follow this execution flow:

    1. Parse user context from Input (if provided)
    2. Review task list and identify current implementation status
    3. Execute tasks in dependency order, following the planned sequence
    4. Implement evaluation infrastructure components systematically
    5. Test and validate each component as it's built
    6. Integrate components into a cohesive evaluation pipeline
    7. Perform end-to-end testing and validation

4. **Implementation Process**:

   a. **Task Execution Strategy**: Follow systematic implementation approach:
      - Execute tasks in dependency order (prerequisites first)
      - Validate each task's acceptance criteria before proceeding
      - Test components individually before integration
      - Document implementation decisions and deviations from plan
      - Update task status and track progress continuously

   b. **Phase-by-Phase Implementation**:

      **Phase 1: Foundation Setup**
      ```bash
      # Environment setup and basic infrastructure
      
      # 1. Create setup.sh script for environment setup
      cat > eval/setup.sh << 'EOF'
      #!/bin/bash
      set -e
      
      echo "Setting up evaluation environment..."
      
      # Create virtual environment using uv
      uv venv eval-env
      source eval-env/bin/activate
      
      # Install core dependencies
      uv pip install \
          "deepeval>=0.21.0" \
          "pandas>=2.0.0" \
          "pyyaml>=6.0" \
          "rich>=13.0.0" \
          "httpx>=0.24.0" \
          "plotly>=5.15.0"
      
      echo "Environment setup complete!"
      EOF
      
      chmod +x eval/setup.sh
      
      # Run the setup script
      ./eval/setup.sh
      
      # 2. Create directory structure
      mkdir -p eval/results eval/checklists
      
      # Create core files
      touch eval/config.yaml
      touch eval/evaluators.py
      touch eval/run_evaluation.py
      touch eval/test_cases.json
      touch eval/spec.md
      touch eval/plan.md
      touch eval/tasks.md
      
      echo "Project structure created successfully!"
      ```

      **Phase 2: Agent Integration**
      ```python
      # Agent connection and integration
      
      class AgentConnector:
          """Base class for agent integration."""
          
          def __init__(self, config: dict):
              self.config = config
              self.agent = None
              
          def connect(self):
              """Establish connection to the agent."""
              # Implementation depends on agent type
              # - Direct import for Python agents
              # - HTTP client for API-based agents
              # - Docker container for isolated agents
              pass
              
          def execute(self, input_data: dict) -> dict:
              """Execute agent with input data and return results."""
              # CRITICAL: Must use real agent, never simulate
              if not self.agent:
                  raise RuntimeError("Agent not connected")
                  
              # Measure execution time
              import time
              start_time = time.time()
              
              try:
                  result = self.agent.process(input_data)
                  execution_time = time.time() - start_time
                  
                  return {
                      "output": result,
                      "execution_time": execution_time,
                      "status": "success",
                      "timestamp": time.time()
                  }
              except Exception as e:
                  execution_time = time.time() - start_time
                  return {
                      "output": None,
                      "execution_time": execution_time,
                      "status": "error",
                      "error": str(e),
                      "timestamp": time.time()
                  }
      ```

      **Phase 3: Evaluation Engine**
      ```python
      # Core evaluation implementation
      
      from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
      from deepeval.test_case import LLMTestCase
      
      class EvaluationEngine:
          """Core evaluation engine using DeepEval framework."""
          
          def __init__(self, config: dict):
              self.config = config
              self.metrics = self._initialize_metrics()
              
          def _initialize_metrics(self):
              """Initialize evaluation metrics based on configuration."""
              metrics = {}
              
              # Standard metrics for LLM agents
              if self.config.get("metrics", {}).get("relevancy", True):
                  metrics["relevancy"] = AnswerRelevancyMetric(
                      threshold=self.config.get("relevancy_threshold", 0.7)
                  )
                  
              if self.config.get("metrics", {}).get("faithfulness", True):
                  metrics["faithfulness"] = FaithfulnessMetric(
                      threshold=self.config.get("faithfulness_threshold", 0.7)
                  )
                  
              return metrics
              
          def evaluate_response(self, test_case: dict, agent_response: dict) -> dict:
              """Evaluate a single agent response."""
              results = {}
              
              # Create DeepEval test case
              eval_case = LLMTestCase(
                  input=test_case["input"],
                  actual_output=agent_response["output"],
                  retrieval_context=test_case.get("context", [])
              )
              
              # Run each metric
              for metric_name, metric in self.metrics.items():
                  try:
                      metric.measure(eval_case)
                      results[metric_name] = {
                          "score": metric.score,
                          "success": metric.success,
                          "reason": metric.reason
                      }
                  except Exception as e:
                      results[metric_name] = {
                          "score": 0.0,
                          "success": False,
                          "reason": f"Evaluation error: {str(e)}"
                      }
                      
              return results
      ```

      **Phase 4: Data Pipeline**
      ```python
      # Data processing and management
      
      import json
      import pandas as pd
      from pathlib import Path
      
      class DataManager:
          """Manage test data and results."""
          
          def __init__(self, eval_dir: Path):
              self.eval_dir = Path(eval_dir)
              self.test_cases_file = self.eval_dir / "test_cases.json"
              self.results_dir = self.eval_dir / "results"
              
          def load_test_cases(self) -> list:
              """Load test cases from JSON file."""
              if not self.test_cases_file.exists():
                  raise FileNotFoundError(f"Test cases file not found: {self.test_cases_file}")
                  
              with open(self.test_cases_file, 'r') as f:
                  data = json.load(f)
                  
              # Handle both array format and object format
              if isinstance(data, list):
                  test_cases = data
              elif isinstance(data, dict) and "test_cases" in data:
                  test_cases = data["test_cases"]
              else:
                  raise ValueError("Invalid test cases format. Expected array or object with 'test_cases' key.")
                  
              # Ensure each case has an ID
              for i, case in enumerate(test_cases):
                  if "id" not in case:
                      case["id"] = f"case_{i+1}"
                      
              return test_cases
              
          def save_results(self, results: list, run_id: str):
              """Save evaluation results."""
              self.results_dir.mkdir(exist_ok=True)
              
              # Save detailed results as JSON
              results_file = self.results_dir / f"{run_id}_detailed.json"
              with open(results_file, 'w') as f:
                  json.dump(results, f, indent=2)
                  
              # Save summary as CSV for analysis
              df = pd.json_normalize(results)
              summary_file = self.results_dir / f"{run_id}_summary.csv"
              df.to_csv(summary_file, index=False)
      ```

   c. **Integration and Testing**: Combine components into working pipeline:
      ```python
      # Main evaluation pipeline
      
      def run_evaluation(config_path: str):
          """Run complete evaluation pipeline."""
          import yaml
          from datetime import datetime
          
          # Load configuration
          with open(config_path, 'r') as f:
              config = yaml.safe_load(f)
              
          # Initialize components
          agent_connector = AgentConnector(config["agent"])
          evaluation_engine = EvaluationEngine(config["evaluation"])
          data_manager = DataManager(Path("eval"))
          
          # Connect to agent
          agent_connector.connect()
          
          # Load test cases
          test_cases = data_manager.load_test_cases()
          print(f"Loaded {len(test_cases)} test cases")
          
          # Run evaluation
          results = []
          run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
          
          for i, test_case in enumerate(test_cases):
              print(f"Processing test case {i+1}/{len(test_cases)}: {test_case['id']}")
              
              # Execute agent
              agent_response = agent_connector.execute(test_case)
              
              # Evaluate response
              if agent_response["status"] == "success":
                  eval_results = evaluation_engine.evaluate_response(test_case, agent_response)
              else:
                  eval_results = {"error": agent_response.get("error", "Unknown error")}
                  
              # Combine results
              result = {
                  "test_case_id": test_case["id"],
                  "agent_response": agent_response,
                  "evaluation": eval_results,
                  "timestamp": datetime.now().isoformat()
              }
              results.append(result)
              
          # Save results
          data_manager.save_results(results, run_id)
          print(f"Evaluation complete. Results saved with run_id: {run_id}")
          
          return results
      ```

5. **Implementation Validation**: For each implemented component:
   - Verify it meets the acceptance criteria from the task list
   - Test with sample data to ensure functionality
   - Check integration with other components
   - Validate error handling and edge cases
   - Ensure no simulation or mocking is present

6. **Quality Assurance Checklist**:
   - [ ] All tasks from task list are implemented
   - [ ] Agent integration uses real agent (no simulation)
   - [ ] Evaluation metrics are computed from actual execution
   - [ ] Error handling is robust and informative
   - [ ] Configuration is externalized and validated
   - [ ] Results are stored in specified format
   - [ ] Code follows project standards and is documented
   - [ ] End-to-end pipeline executes successfully

7. **Documentation and Handoff**: Create implementation documentation:
   - Setup and installation instructions
   - Configuration guide and examples
   - Usage instructions and CLI reference
   - Troubleshooting guide and common issues
   - Code architecture and component overview

8. Report completion with implementation status, component overview, and readiness for the next phase (`/evalkit.insights`).

## General Guidelines

### Implementation Principles

- **Real Agent Focus**: Always integrate with actual agent, never simulate or mock
- **Incremental Development**: Build and test components incrementally
- **Configuration-Driven**: Externalize all settings and parameters
- **Error Resilience**: Handle failures gracefully with clear error messages
- **Observability**: Include comprehensive logging and monitoring

### Code Quality Standards

**Required Standards**:
- Clear, descriptive variable and function names
- Comprehensive error handling with specific error messages
- Logging at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Type hints for function parameters and return values
- Docstrings for all classes and public methods
- End-to-end evaluation testing

**Code Organization**:
- Separate concerns into focused modules
- Use dependency injection for testability
- Follow consistent naming conventions
- Keep functions small and focused
- Minimize coupling between components

### Testing Strategy

**Component Testing**:
- Integration tests for component interactions
- Mock external dependencies (but never the agent under test)
- Test error conditions and edge cases

**End-to-End Testing**:
- Full pipeline execution with sample data
- Validation of output formats and content
- Performance testing with realistic data volumes
- Error recovery and failure scenarios

### Common Implementation Pitfalls

**Avoid These Mistakes**:
- **Agent Simulation**: Never mock or simulate the agent being evaluated
- **Hardcoded Values**: Don't embed configuration in code
- **Silent Failures**: Always log errors and provide clear error messages
- **Monolithic Code**: Break large functions into smaller, testable units
- **Missing Validation**: Always validate inputs and configuration
- **Poor Error Messages**: Provide actionable error messages with context

**Best Practices**:
- **Fail Fast**: Validate configuration and dependencies early
- **Defensive Programming**: Check assumptions and handle edge cases
- **Clear Logging**: Log important events and decisions
- **Graceful Degradation**: Continue evaluation even if some tests fail
- **Resource Cleanup**: Properly close files, connections, and resources
