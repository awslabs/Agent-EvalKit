#!/usr/bin/env python3
"""
generate_data.py
Generate test cases using AI-powered dataset generator with topic planning.

Usage:
    python generator/generate_data.py --plan eval/eval-plan.md --output eval/test-cases.jsonl --num-cases 10 [--num-topics 5] [--pretty]

Features:
- Extracts context and task description from evaluation plan
- Uses TopicPlanner for diverse test case coverage
- Generates test cases via LLM with strands-agents
- Outputs JSONL format (one test case per line)
"""

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

# Add parent directory to path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.dataset_generator import DatasetGenerator


def extract_context_from_plan(plan_content: str) -> str:
    """Extract context from evaluation plan."""
    # Look for context sections in the plan
    # This is a simple extraction - customize based on your plan format
    context_match = re.search(
        r'(?:## Context|## Background|## Description)(.*?)(?=##|$)',
        plan_content,
        re.DOTALL | re.IGNORECASE
    )
    if context_match:
        return context_match.group(1).strip()
    return plan_content[:1000]  # Fallback: first 1000 chars


def extract_task_description(plan_content: str) -> str:
    """Extract task description from evaluation plan."""
    # Look for task description sections
    task_match = re.search(
        r'(?:## Task|## Objective|## Goal)(.*?)(?=##|$)',
        plan_content,
        re.DOTALL | re.IGNORECASE
    )
    if task_match:
        return task_match.group(1).strip()
    return "Perform the task as specified in the evaluation plan"


def extract_num_topics_from_plan(plan_content: str) -> int | None:
    """Extract number of topics from evaluation plan."""
    # Look for topic count specifications
    topic_match = re.search(
        r'(?:topics?|scenarios?|areas?):\s*(\d+)',
        plan_content,
        re.IGNORECASE
    )
    if topic_match:
        return int(topic_match.group(1))
    return None


async def main():
    parser = argparse.ArgumentParser(
        description='Generate test cases with AI-powered dataset generator'
    )
    parser.add_argument(
        '--plan', '-p',
        required=True,
        help='Path to evaluation plan markdown file (e.g., eval/eval-plan.md)'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output path for test cases JSONL file (e.g., eval/test-cases.jsonl)'
    )
    parser.add_argument(
        '--num-cases', '-n',
        type=int,
        default=10,
        help='Number of test cases to generate (default: 10)'
    )
    parser.add_argument(
        '--num-topics', '-t',
        type=int,
        default=None,
        help='Number of topics for diverse coverage (default: extract from plan or 5)'
    )
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty-print JSON output'
    )
    
    args = parser.parse_args()
    
    # Read evaluation plan
    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"[ERROR] Evaluation plan not found: {plan_path}", file=sys.stderr)
        sys.exit(2)
    
    with plan_path.open('r', encoding='utf-8') as f:
        plan_content = f.read()
    
    # Extract information from plan
    context = extract_context_from_plan(plan_content)
    task_description = extract_task_description(plan_content)
    
    # Determine num_topics: CLI arg > plan > default to 5
    num_topics = args.num_topics
    if num_topics is None:
        num_topics = extract_num_topics_from_plan(plan_content)
    if num_topics is None:
        num_topics = 5
    
    print(f"Generating {args.num_cases} test cases with {num_topics} topics...")
    print(f"Context length: {len(context)} chars")
    print(f"Task: {task_description[:100]}...")
    
    # Initialize generator
    generator = DatasetGenerator(input_type=str, output_type=str)
    
    # Generate dataset with topic planning
    dataset = await generator.from_context_async(
        context=context,
        task_description=task_description,
        num_cases=args.num_cases,
        num_topics=num_topics
    )
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as JSONL
    with output_path.open('w', encoding='utf-8') as f:
        for case in dataset.cases:
            if args.pretty:
                f.write(json.dumps(case.model_dump(), ensure_ascii=False, indent=2))
                f.write('\n')
            else:
                f.write(json.dumps(case.model_dump(), ensure_ascii=False))
                f.write('\n')
    
    print(f"✓ Generated {len(dataset.cases)} test cases → {output_path}")
    print(f"  Topics used: {num_topics}")
    print(f"  Output format: JSONL (one case per line)")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Generation interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
