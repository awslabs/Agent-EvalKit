# QA Agent Faithfulness Evaluation

This directory contains the evaluation framework for assessing the QA+Search agent's answer faithfulness and relevancy.

## Overview

The evaluation measures how well the agent's answers are grounded in search results retrieved from Tavily, focusing on:
- **Faithfulness**: Whether answers are factually consistent with retrieved search results
- **Answer Relevancy**: Whether answers directly address the user's query

## Directory Structure

```
eval/
├── README.md                    # This file
├── eval-plan.md                 # Detailed evaluation plan and requirements
├── test-cases.jsonl             # Test cases for evaluation
├── metrics.py                   # Metric implementations and trace extraction
├── agent_runner.py              # Agent execution script
├── run_evaluation.py            # Main evaluation orchestration
├── traces/                      # Processed trace files
│   └── <traceId>.json
├── results/                     # Evaluation results
│   └── evaluation_results_*.json
└── otel-traces.jsonl            # Raw OTEL traces (generated during execution)
```

## Prerequisites

- Python 3.11+
- AWS credentials configured for Bedrock access
- Virtual environment with dependencies installed

## Running the Evaluation

### Step 1: Ensure Environment is Set Up

```bash
# From repository root
source .venv/bin/activate
```

### Step 2: Run Evaluation

```bash
# Run evaluation on processed traces
python eval/run_evaluation.py --input eval/traces/ --output eval/results/
```

### Arguments

- `--input`: Directory containing processed trace files (default: `eval/traces/`)
- `--output`: Directory to save evaluation results (default: `eval/results/`)

## Metrics

### Faithfulness Metric
- **Threshold**: 0.7
- **Purpose**: Measures whether the agent's answer contains only claims that can be verified from the search results
- **Method**: LLM-as-Judge using AWS Bedrock Claude Sonnet via LiteLLM
- **Evaluation**: Analyzes if claims in the answer are grounded in retrieval context

### Answer Relevancy Metric
- **Threshold**: 0.7
- **Purpose**: Measures how well the answer addresses the original user query
- **Method**: LLM-as-Judge using AWS Bedrock Claude Sonnet via LiteLLM
- **Evaluation**: Assesses semantic relevance between query and response

## Understanding Results

Results are saved as JSON files in `eval/results/` with the following structure:

```json
{
  "evaluation_timestamp": "2025-11-20T21:49:18...",
  "total_test_cases": 2,
  "metrics_used": ["FaithfulnessMetric", "AnswerRelevancyMetric"],
  "summary": {
    "faithfulness": {
      "avg_score": 0.694,
      "min_score": 0.636,
      "max_score": 0.750,
      "pass_rate": 0.5
    },
    "relevancy": {
      "avg_score": 0.988,
      "min_score": 0.976,
      "max_score": 1.0,
      "pass_rate": 1.0
    }
  },
  "test_cases": [...]
}
```

### Interpreting Scores

- **Score Range**: 0.0 to 1.0 (higher is better)
- **Pass Threshold**: 0.7
- **Pass Rate**: Percentage of test cases that meet or exceed the threshold

### Example Results

From the latest evaluation:
- **Faithfulness**: 69.4% average score, 50% pass rate
  - Indicates some hallucinations or unsupported claims in answers
- **Answer Relevancy**: 98.8% average score, 100% pass rate
  - Indicates answers are highly relevant to queries

## Trace Structure

Processed traces (`eval/traces/<traceId>.json`) contain:
- User queries from `gen_ai_prompts`
- Agent answers from `gen_ai_completions`
- Search results from `execute_tool` spans with `web_search` tool

## Troubleshooting

### AWS Credentials
If you see Bedrock access errors:
```bash
# Ensure AWS credentials are configured
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### Missing Dependencies
```bash
# Reinstall dependencies
uv pip install -r requirements.txt
```

### No Traces Found
Ensure traces have been collected and processed:
```bash
# Check for trace files
ls eval/traces/
```

## Modifying Evaluation

### Changing Thresholds
Edit `eval/run_evaluation.py`:
```python
faithfulness_metric = create_faithfulness_metric(threshold=0.8)  # Change threshold
relevancy_metric = create_answer_relevancy_metric(threshold=0.8)
```

### Adding New Test Cases
Edit `eval/test-cases.jsonl` and add new lines:
```jsonl
{"test_id": "new_001", "scenario": "...", "query": "...", "description": "...", "expected_behavior": "..."}
```

Then re-run the agent and evaluation pipeline.

## Next Steps

After running evaluation, you can:
1. Analyze results in `eval/results/evaluation_results_*.json`
2. Review specific failing test cases to identify improvement opportunities
3. Adjust agent prompts or search strategies based on findings
4. Re-run evaluation to measure improvements

For detailed evaluation methodology and planning, see `eval-plan.md`.
