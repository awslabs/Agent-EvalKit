#!/usr/bin/env python3
"""
Main evaluation orchestration script.

Loads processed traces, creates test cases, applies metrics, and generates results.
"""
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from deepeval import evaluate

from metrics import (
    create_test_case_from_trace,
    create_faithfulness_metric,
    create_answer_relevancy_metric
)


def load_traces_from_directory(traces_dir: Path) -> List[Path]:
    """Load all trace files from the traces directory."""
    trace_files = list(traces_dir.glob("*.json"))
    print(f"Found {len(trace_files)} trace files in {traces_dir}")
    return trace_files


def run_evaluation(traces_dir: Path, output_dir: Path):
    """
    Run evaluation on all traces.

    Args:
        traces_dir: Directory containing processed trace files
        output_dir: Directory to save evaluation results
    """
    print("\n" + "=" * 60)
    print("QA AGENT FAITHFULNESS EVALUATION")
    print("=" * 60 + "\n")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load trace files
    trace_files = load_traces_from_directory(traces_dir)
    if not trace_files:
        print("Error: No trace files found!")
        return

    # Create test cases from traces
    print("\nCreating test cases from traces...")
    test_cases = []
    trace_metadata = {}

    for trace_file in trace_files:
        print(f"  Processing: {trace_file.name}")
        test_case = create_test_case_from_trace(trace_file)
        if test_case:
            test_cases.append(test_case)
            trace_metadata[len(test_cases) - 1] = {
                "trace_id": trace_file.stem,
                "trace_file": str(trace_file)
            }
        else:
            print(f"    Warning: Failed to create test case from {trace_file.name}")

    if not test_cases:
        print("\nError: No valid test cases created!")
        return

    print(f"\nCreated {len(test_cases)} test cases")

    # Create metrics
    print("\nInitializing metrics...")
    faithfulness_metric = create_faithfulness_metric(threshold=0.7)
    relevancy_metric = create_answer_relevancy_metric(threshold=0.7)

    metrics = [faithfulness_metric, relevancy_metric]
    print(f"  - Faithfulness Metric (threshold: 0.7)")
    print(f"  - Answer Relevancy Metric (threshold: 0.7)")

    # Run evaluation
    print("\n" + "=" * 60)
    print("RUNNING EVALUATION")
    print("=" * 60 + "\n")

    try:
        results = evaluate(
            test_cases=test_cases,
            metrics=metrics
        )
    except Exception as e:
        print(f"\nError during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return

    # Save detailed results
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60 + "\n")

    results_data = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "total_test_cases": len(test_cases),
        "metrics_used": ["FaithfulnessMetric", "AnswerRelevancyMetric"],
        "test_cases": []
    }

    for idx, test_case in enumerate(test_cases):
        metadata = trace_metadata.get(idx, {})

        test_case_result = {
            "test_case_id": idx,
            "trace_id": metadata.get("trace_id"),
            "trace_file": metadata.get("trace_file"),
            "input": test_case.input,
            "actual_output": test_case.actual_output[:500] + "..." if len(test_case.actual_output) > 500 else test_case.actual_output,
            "retrieval_context_count": len(test_case.retrieval_context) if test_case.retrieval_context else 0,
            "metrics": {}
        }

        # Add metric scores (DeepEval stores these on test_case after evaluation)
        for metric in metrics:
            metric_name = metric.__class__.__name__
            # Try to get score from the metric after measurement
            try:
                metric.measure(test_case)
                test_case_result["metrics"][metric_name] = {
                    "score": metric.score,
                    "threshold": metric.threshold,
                    "passed": metric.score >= metric.threshold if metric.score is not None else False,
                    "reason": metric.reason if hasattr(metric, 'reason') else None
                }
            except Exception as e:
                test_case_result["metrics"][metric_name] = {
                    "error": str(e)
                }

        results_data["test_cases"].append(test_case_result)

    # Calculate summary statistics
    faithfulness_scores = []
    relevancy_scores = []

    for tc in results_data["test_cases"]:
        if "FaithfulnessMetric" in tc["metrics"] and "score" in tc["metrics"]["FaithfulnessMetric"]:
            score = tc["metrics"]["FaithfulnessMetric"]["score"]
            if score is not None:
                faithfulness_scores.append(score)

        if "AnswerRelevancyMetric" in tc["metrics"] and "score" in tc["metrics"]["AnswerRelevancyMetric"]:
            score = tc["metrics"]["AnswerRelevancyMetric"]["score"]
            if score is not None:
                relevancy_scores.append(score)

    results_data["summary"] = {
        "faithfulness": {
            "avg_score": sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else None,
            "min_score": min(faithfulness_scores) if faithfulness_scores else None,
            "max_score": max(faithfulness_scores) if faithfulness_scores else None,
            "pass_rate": sum(1 for s in faithfulness_scores if s >= 0.7) / len(faithfulness_scores) if faithfulness_scores else None
        },
        "relevancy": {
            "avg_score": sum(relevancy_scores) / len(relevancy_scores) if relevancy_scores else None,
            "min_score": min(relevancy_scores) if relevancy_scores else None,
            "max_score": max(relevancy_scores) if relevancy_scores else None,
            "pass_rate": sum(1 for s in relevancy_scores if s >= 0.7) / len(relevancy_scores) if relevancy_scores else None
        }
    }

    # Save results
    results_file = output_dir / f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"Results saved to: {results_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"\nFaithfulness Metric:")
    print(f"  Average Score: {results_data['summary']['faithfulness']['avg_score']:.3f}" if results_data['summary']['faithfulness']['avg_score'] else "  Average Score: N/A")
    print(f"  Pass Rate: {results_data['summary']['faithfulness']['pass_rate']*100:.1f}%" if results_data['summary']['faithfulness']['pass_rate'] is not None else "  Pass Rate: N/A")

    print(f"\nAnswer Relevancy Metric:")
    print(f"  Average Score: {results_data['summary']['relevancy']['avg_score']:.3f}" if results_data['summary']['relevancy']['avg_score'] else "  Average Score: N/A")
    print(f"  Pass Rate: {results_data['summary']['relevancy']['pass_rate']*100:.1f}%" if results_data['summary']['relevancy']['pass_rate'] is not None else "  Pass Rate: N/A")

    print("\n" + "=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run QA agent faithfulness evaluation")
    parser.add_argument(
        "--input",
        type=str,
        default="eval/traces/",
        help="Directory containing processed trace files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="eval/results/",
        help="Directory to save evaluation results"
    )

    args = parser.parse_args()

    traces_dir = Path(args.input)
    output_dir = Path(args.output)

    if not traces_dir.exists():
        print(f"Error: Traces directory not found: {traces_dir}")
        return 1

    run_evaluation(traces_dir, output_dir)
    return 0


if __name__ == "__main__":
    exit(main())
