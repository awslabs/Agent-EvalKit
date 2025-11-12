# Using DeepEval for Evaluation

## Trace-Based Evaluation Foundation

**Primary Input**: Processed traces from `eval/traces/<traceId>.json` files

**Understanding Trace Structure**: Load and examine a processed trace from `eval/traces/<traceId>.json` to understand the actual trace structure before implementation.

**Core Evaluation Principles**:

1. **Trace-to-TestCase Conversion**: Transform processed traces into DeepEval LLMTestCase objects
2. **LLMTestCase as Evaluation Unit**: Each evaluation operation (E2E run, single step, or single tool call) becomes one LLMTestCase
3. **Built-in Metrics Priority**: Use DeepEval built-in metrics when available, custom metrics (BaseMetric + G-Eval) only when needed
4. **Multi-Granularity Support**: Extraction functions must build test cases at multiple granularities from a single trace as needed


## Code Patterns for Trace-Based Evaluation with DeepEval

This section summarizes the key code patterns that can be adapted for other trace-based evaluation requirements and metrics.

### Configuration Pattern

```yaml
# In eval/config.yaml
model:
  name: "bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0"

evaluation:
  metrics:
    - "metric_name_1"
    - "metric_name_2"
  thresholds:
    metric_name_1: 0.7
    metric_name_2: 0.7

traces:
  input_dir: "path/to/traces"

results:
  output_dir: "path/to/results"
```

### Trace Extraction Pattern

```python
# In eval/extraction_utils.py
import json
from deepeval.test_case import LLMTestCase, ToolCall

def extract_user_input(trace_data: Dict[str, Any]) -> str:
    """Extract user input from trace structure."""
    spans = trace_data.get("spans", [])
    
    # Pattern: Navigate trace hierarchy to find input
    for span in spans:
        if span.get("entity_name") == "TARGET_ENTITY":
            # Pattern: Parse nested JSON structures
            entity_input = span.get("entity_input", "")
            try:
                input_data = json.loads(entity_input)
                # Extract specific fields based on trace format
                return extract_from_nested_structure(input_data)
            except (json.JSONDecodeError, KeyError):
                continue
    return ""

def extract_tool_calls(trace_data: Dict[str, Any]) -> List[ToolCall]:
    """Extract tool calls from trace spans."""
    tool_calls = []
    spans = trace_data.get("spans", [])
    
    for span in spans:
        # Pattern: Look for tool usage indicators
        if "gen_ai_prompts" in span and "gen_ai_completions" in span:
            prompts = span.get("gen_ai_prompts", [])
            
            # Pattern: Parse tool use/result pairs
            for prompt in prompts:
                if contains_tool_result(prompt):
                    tool_call = create_tool_call_from_prompt(prompt)
                    if tool_call:
                        tool_calls.append(tool_call)
    
    return tool_calls

def load_trace_to_test_case(file_path: str) -> LLMTestCase:
    """Main pattern: Convert trace file to DeepEval test case."""
    with open(file_path, 'r') as f:
        trace_data = json.load(f)
    
    # Pattern: Extract key components
    user_input = extract_user_input(trace_data)
    final_response = extract_final_response(trace_data)
    tool_calls = extract_tool_calls(trace_data)
    
    # Pattern: Create standardized test case
    return LLMTestCase(
        input=user_input,
        actual_output=final_response,
        tools_called=tool_calls
    )
```

### Metrics Definition Pattern

```python
# In eval/metrics.py
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval, BaseMetric
from deepeval.models import LiteLLMModel
import os
import litellm

# Configure LiteLLM to drop unsupported parameters for Bedrock
litellm.drop_params = True

# Configure default model
DEFAULT_MODEL = LiteLLMModel(model="bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0")

class CustomMetric(BaseMetric):
    """Pattern: Custom metric implementation."""
    
    def __init__(self, model=DEFAULT_MODEL):
        # Pattern: GEval configuration
        self.judge = GEval(
            name="Metric Name",
            criteria=(
                "Clear evaluation criteria describing what to assess "
                "and how to score the performance."
            ),
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
                # Add other params as needed
            ],
            model=model,
        )

    def measure(self, test_case: LLMTestCase) -> float:
        # Pattern: Optional context setup
        if test_case.context is None:
            test_case.context = {}
        test_case.context["additional_info"] = test_case.tools_called
        
        return self.judge.measure(test_case)

    def is_successful(self, score: float) -> bool:
        return score >= 0.7  # Configurable threshold

def get_metrics(config: dict = None):
    """Pattern: Metric factory function with config-based model setup."""
    # Pattern: Configure model from config.yaml
    if config and "model" in config:
        model_config = config["model"]
        
        # Create model from config
        model = LiteLLMModel(
            model=model_config.get("name", "bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0")
        )
    else:
        # Fallback to default model
        model = DEFAULT_MODEL
    
    return [
        CustomMetric1(model=model),
        CustomMetric2(model=model)
    ]
```

### Main Evaluation Script Pattern

```python
# In eval/run_evaluation.py
import os
import json
import yaml
import argparse
from pathlib import Path

def load_config(config_path: str) -> Dict[str, Any]:
    """Pattern: YAML configuration loading."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def evaluate_trace(trace_path: str, config: Dict[str, Any]) -> Dict[str, float]:
    """Pattern: Single trace evaluation."""
    print(f"Evaluating trace: {trace_path}")
    
    # Pattern: Load and convert trace
    test_case = load_trace_to_test_case(trace_path)
    
    # Pattern: Get configured metrics
    metrics = get_metrics(config)
    
    # Pattern: Run evaluation with error handling
    results = {}
    for metric in metrics:
        try:
            score = metric.measure(test_case)
            results[metric.judge.name] = score
            print(f"{metric.judge.name}: {score:.3f}")
        except Exception as e:
            print(f"Error evaluating {metric.judge.name}: {e}")
            results[metric.judge.name] = 0.0
    
    return results

def main():
    """Pattern: CLI interface with argparse."""
    parser = argparse.ArgumentParser(description="Evaluate traces")
    parser.add_argument("--trace", type=str, help="Single trace file")
    parser.add_argument("--config", type=str, default="config.yaml")
    parser.add_argument("--output", type=str, help="Output file")
    
    args = parser.parse_args()
    
    # Pattern: Configuration setup
    config = load_config(args.config)
    
    # Pattern: Setup model configuration from config
    # (This is handled in get_metrics function)
    
    if args.trace:
        # Pattern: Single file evaluation
        results = evaluate_trace(args.trace, config)
        
        # Pattern: Results summary with thresholds
        print("\n" + "="*50)
        print("EVALUATION SUMMARY")
        print("="*50)
        
        for metric_name, score in results.items():
            # Pattern: Get threshold from config with fallback
            threshold = config.get("evaluation", {}).get("thresholds", {}).get(
                metric_name.lower().replace(" ", "_"), 0.7
            )
            status = "PASS" if score >= threshold else "FAIL"
            print(f"{metric_name}: {score:.3f} ({status})")
        
        # Pattern: Optional result saving
        if args.output:
            output_data = {
                "trace_file": args.trace,
                "results": results,
                "config": config
            }
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
    
    else:
        # Pattern: Batch processing
        input_dir = config.get("traces", {}).get("input_dir", "traces")
        trace_files = list(Path(input_dir).glob("*.json"))
        
        all_results = {}
        for trace_file in trace_files:
            try:
                results = evaluate_trace(str(trace_file), config)
                all_results[trace_file.name] = results
            except Exception as e:
                all_results[trace_file.name] = {"error": str(e)}
        
        # Pattern: Batch results saving
        output_dir = config.get("results", {}).get("output_dir", "results")
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, "results.json"), 'w') as f:
            json.dump({"config": config, "results": all_results}, f, indent=2)

if __name__ == "__main__":
    main()
```

### Key Adaptation Points

1. **Trace Structure**: Modify `extract_*` functions in `extraction_utils.py` based on the current trace format
2. **Metrics**: Create custom metrics by extending `BaseMetric` and defining appropriate `GEval` criteria
3. **Model Configuration**: Adjust model settings in config.yaml and metrics.py
4. **Input/Output Paths**: Configure trace directories and output locations
5. **Evaluation Parameters**: Choose appropriate `LLMTestCaseParams` for the proposed metrics