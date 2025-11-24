#!/usr/bin/env python3
"""
Agent runner script that executes the QA agent against test cases and collects traces.
"""
import sys
import json
import argparse
from pathlib import Path

# Add the qa_agent module to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "qa_agent"))

# Import the instrumented agent
from qa_agent import agent


def load_test_cases(input_file: str) -> list[dict]:
    """Load test cases from JSONL file."""
    test_cases = []
    with open(input_file, "r") as f:
        for line in f:
            if line.strip():
                test_cases.append(json.loads(line))
    return test_cases


def run_agent_on_test_case(test_case: dict) -> dict:
    """Run the agent on a single test case and return results."""
    test_id = test_case["test_id"]
    query = test_case["query"]

    print(f"\n{'='*60}")
    print(f"Running test: {test_id}")
    print(f"Query: {query}")
    print(f"{'='*60}")

    try:
        # Run the agent
        answer = agent(query)

        print(f"\nAnswer: {answer}\n")

        return {
            "test_id": test_id,
            "query": query,
            "answer": str(answer),  # Convert to string for JSON serialization
            "status": "success",
            "error": None,
        }
    except Exception as e:
        print(f"\nError running agent: {e}\n")
        return {"test_id": test_id, "query": query, "answer": None, "status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Run QA agent on test cases")
    parser.add_argument("--input", required=True, help="Path to test cases JSONL file")
    args = parser.parse_args()

    print(f"Loading test cases from: {args.input}")
    test_cases = load_test_cases(args.input)
    print(f"Loaded {len(test_cases)} test cases")

    results = []
    for test_case in test_cases:
        result = run_agent_on_test_case(test_case)
        results.append(result)

    # Print summary
    print(f"\n{'='*60}")
    print(f"EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total test cases: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"Failed: {sum(1 for r in results if r['status'] == 'error')}")
    print(f"{'='*60}\n")

    # Save results
    # results_file = Path(__file__).parent / "agent_execution_results.json"
    # with open(results_file, "w") as f:
    #     json.dump(results, f, indent=2)
    # print(f"Results saved to: {results_file}")


if __name__ == "__main__":
    main()
