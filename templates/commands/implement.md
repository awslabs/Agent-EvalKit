---
description: Execute implementation tasks according to the established plan
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-design --include-design
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.implement` in the triggering message **is** additional context or specific implementation requirements. This command executes the implementation tasks according to the established plan.

Given that context, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and IMPLEMENTATION_STATUS. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

2. Load the current evaluation design (`eval/eval-design.md`) to understand the task structure and requirements.

3. Follow this execution flow:

    1. Parse user context from Input (if provided)
    2. Review evaluation design and identify task groups
    3. Execute tasks according to the design structure (based on selected modules):
       - Setup Project Structure (always required)
       - Instrumentation Setup (if agent lacks tracing)
       - Test Case Generation (if no existing test cases available)
       - Trace Collection (if no exsiting traces available)
       - Core Evaluation Pipeline Module (always required)
       - Results & Analysis (always required)
       - Code Review & Testing (always required)
    4. Test and validate each component as it's built
    5. Ensure all evaluation uses actual agent execution, no mocking

## Implementation Process

### Task Execution Strategy

Follow the established design structure systematically:
- Execute only the modules marked as required in `eval/eval-design.md`
- Validate each component before proceeding
- Use actual agent execution, never mock

### Leveraging Context7 MCP for Latest Library Information

**IMPORTANT**: EvalKit projects include Context7 MCP server for accessing the latest documentation and usage patterns. Use this built-in capability to ensure you're implementing with current best practices:

- **Before implementing evaluation libraries**: Ask Context7 for the latest usage patterns, API changes, and best practices for libraries like Langfuse, DeepEval, LiteLLM, or other open source frameworks
- **For dependency management**: Get current version recommendations and compatibility information
- **For integration patterns**: Access up-to-date examples and implementation guides
- **For troubleshooting**: Get current solutions for common integration issues

Example Context7 queries:
- "What's the latest DeepEval API for custom metrics?"
- "Show me current best practices for Langfuse trace fetch setup"
- "How to properly configure evaluation environments with current dependency versions?"

This ensures your implementation uses the most current approaches and avoids deprecated patterns.

### Key Implementation Examples

#### Agent Integration Pattern
```python
class AgentConnector:
    """Base class for agent integration."""
    
    def __init__(self, config: dict):
        self.config = config
        self.agent = None
        
    def execute(self, input_data: dict) -> dict:
        """Execute agent with input data and return results."""
        # CRITICAL: Must use real agent, never mock
        if not self.agent:
            raise RuntimeError("Agent not connected")
            
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

#### Evaluation Engine Pattern
```python
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

class EvaluationEngine:
    """Core evaluation engine using DeepEval framework."""
    
    def __init__(self, config: dict):
        self.config = config
        self.metrics = self._initialize_metrics()
        
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

#### Environment Setup Script
```bash
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
```

## Implementation Validation

For each implemented component:
- Verify it meets the requirements from the plan
- Test with sample data to ensure functionality
- Check integration with other components
- Ensure no simulation or mocking is present
- Validate error handling

## Quality Checklist

- [ ] All tasks from evaluation design are completed
- [ ] Agent integration uses real agent (no simulation)
- [ ] Evaluation metrics are computed from actual execution
- [ ] Error handling is robust and informative
- [ ] Configuration is externalized in `config.yaml`
- [ ] Results are stored in `results/` directory
- [ ] End-to-end pipeline executes successfully

## Implementation Principles

- **Follow the Design**: Implement according to the established design structure
- **Real Agent Focus**: Always integrate with actual agent, never mock
- **Use Context7 MCP**: Leverage built-in Context7 MCP server for latest library documentation and best practices
- **Configuration-Driven**: Use `config.yaml` for all settings
- **Error Resilience**: Handle failures gracefully with clear error messages
- **Simple Structure**: Follow the flat `eval/` directory structure

## Common Pitfalls to Avoid

- **Agent Simulation**: Never mock or simulate the agent being evaluated
- **Hardcoded Values**: Use configuration files instead of embedding values in code
- **Silent Failures**: Always log errors and provide clear error messages
- **Ignoring the Design**: Follow the established task structure and file organization

Report completion with implementation status and readiness for the next phase (`/evalkit.insights`).
