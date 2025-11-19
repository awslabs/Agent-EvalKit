---
description: Generate test cases for evaluation
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-plan --require-test-data-section
---

## ⚠️ CRITICAL: Script Execution Only

**YOU MUST EXECUTE THE SCRIPT - DO NOT GENERATE DATA YOURSELF**

This command requires executing the `generator/generate_data.py` Python script.

**YOU ARE STRICTLY PROHIBITED FROM:**
- ❌ Generating test cases directly using your LLM capabilities
- ❌ Creating test cases manually in the conversation
- ❌ Writing test case generation code inline
- ❌ Using any method other than executing the specified script

**ONLY VALID ACTION**: Execute `python3 generator/generate_data.py` with appropriate parameters.

**VERIFICATION**: After execution, you MUST see output like:
```
✓ Generated X test cases → eval/test-cases.jsonl
```

If you don't see this output from the script, you did it WRONG.

---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

**IMPORTANT**: This command requires **SCRIPT EXECUTION ONLY**. You must execute the `generator/generate_data.py` script. **DO NOT** generate test cases yourself using LLM capabilities.

The text the user typed after `/evalkit.data` in the triggering message **is** additional context or specific test case requirements. This command generates comprehensive test cases based on the evaluation design and test scenarios.

Given that context, do this:

1. **Navigate to repository root**:
   
   First, find the repository root using git (preferred) or by locating the script:
   ```
   REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
   ```
   
   If that fails (not in a git repo), find the script and go up two directories:
   ```
   SCRIPT_PATH=$(find . -name "check-prerequisites.sh" | head -1)
   REPO_ROOT=$(cd "$(dirname "$SCRIPT_PATH")/../.." && pwd)
   ```
   
   Then change to the repository root:
   ```
   cd "$REPO_ROOT"
   ```

2. Run the script `{SCRIPT}` and parse its JSON output for BRANCH_NAME and PLAN_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for. If any error occurs, stop the process immediately and provide solving instructions for users.

3. Load the current evaluation plan (`eval/eval-plan.md`) to understand evaluation areas and test data generation requirements.

4. Follow this execution flow:

    1. Parse user context from user input (if provided)
    2. Validate that the evaluation plan contains a "Test Data Generation" section; update the evaluation plan if it does not align with the user's input (if provided); add entry to Appendix > User Input Tracker in eval-plan.md:
       - `/evalkit.data`: [User input from $ARGUMENTS, or "Not found"]
    3. **EXECUTE THE GENERATOR SCRIPT (Required)**:
       
       **CRITICAL**: You MUST execute this exact command. Do not attempt to generate test cases yourself.
       
       a. **Ensure strands-agents is installed**: 
          ```bash
          pip install strands-agents strands-agents-tools
          ```
       
       b. **Execute the script** (DO NOT SKIP THIS):
          ```bash
          python3 generator/generate_data.py --plan eval/eval-plan.md --output eval/test-cases.jsonl --num-cases 10 --num-topics 5 --pretty
          ```
       
       **DO NOT**:
       - ❌ Generate test cases using your own LLM capabilities
       - ❌ Create test cases manually in this conversation
       - ❌ Use any other method besides executing the script above
       
       **ONLY** execute the script above. The script will:
       - Extract context and task description from the evaluation plan
       - Determine number of topics (from CLI arg > plan > default to 5)
       - Use TopicPlanner to create diverse topic coverage
       - Generate test cases via LLM with strands-agents
       - Save results to `eval/test-cases.jsonl` in JSONL format (one case per line)
    
    4. **VERIFY Script Execution**:
       
       After running the script, verify:
       - ✅ The script executed (not bypassed)
       - ✅ File `eval/test-cases.jsonl` was created by the script
       - ✅ Terminal output shows: `✓ Generated X test cases → eval/test-cases.jsonl`
       - ✅ File contains JSONL format (one test case per line)
       
       **If you generated data any other way, you did it WRONG. Start over and execute the script.**

5. Report completion with test case count, coverage summary, and readiness for trace setup and collection (`/evalkit.trace`).

## General Guidelines

1. **Prioritize user-specific data requests**: User input takes precedence over the established evaluation plan - always honor specific user requirements and constraints. Update the evaluation plan if needed.

## Using Dataset Generator

The Agent-EvalKit includes an AI-powered dataset generator that creates test cases using LLM-based generation with automatic topic planning.

### Prerequisites

Ensure strands-agents is installed:
```bash
pip install strands-agents strands-agents-tools
```

### Generate Test Cases

Run the generator CLI script:

```bash
python3 generator/generate_data.py --plan eval/eval-plan.md --output eval/test-cases.jsonl --num-cases 10 --num-topics 5 --pretty
```

**Parameters:**
- `--plan, -p`: Path to evaluation plan markdown file (required)
- `--output, -o`: Output path for test cases JSONL file (required)
- `--num-cases, -n`: Number of test cases to generate (default: 10)
- `--num-topics, -t`: Number of topics for coverage (default: extract from plan or 5)
- `--pretty`: Pretty-print JSON output (optional)

**The script will:**
1. Read the evaluation plan from `eval/eval-plan.md`
2. Extract context, task description, and topic count
3. Use TopicPlanner to generate diverse topic coverage
4. Generate test cases via LLM using strands-agents
5. Save results to `eval/test-cases.jsonl` in JSONL format

**Example output:**
```
Generating 10 test cases with 5 topics...
Context length: 1234 chars
Task: Handle customer support inquiries...
✓ Generated 10 test cases → eval/test-cases.jsonl
  Topics used: 5
  Output format: JSONL (one case per line)
```

### Integration with /evalkit.data Workflow

When processing `/evalkit.data`, execute the CLI script:

```python
import subprocess

# Run data generator
result = subprocess.run([
    "python3", "generator/generate_data.py",
    "--plan", "eval/eval-plan.md",
    "--output", "eval/test-cases.jsonl",
    "--num-cases", "15",
    "--num-topics", "5",
    "--pretty"
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"Error: {result.stderr}")
else:
    print(result.stdout)
```

### Configuration Options

**DatasetGenerator Parameters:**
- `input_type`: Type of input (e.g., str, dict)
- `output_type`: Type of expected output
- `include_expected_output`: Include expected outputs (default: True)
- `model`: Strands model identifier (optional)
- `max_parallel_num_cases`: Max parallel generation (default: 10)

**from_context_async Parameters:**
- `context`: Context information for test generation (from eval plan)
- `task_description`: Task description (from eval plan)
- `num_cases`: Total number of test cases to generate
- `num_topics`: Number of topics for diverse coverage (default: 5, extract from plan if specified)

### Topic Planning Behavior

When `num_topics` is provided:
1. TopicPlanner analyzes the context
2. Generates diverse topics for comprehensive coverage
3. Distributes test cases across topics
4. Ensures varied difficulty levels and scenarios

**Best Practice:** Always check the evaluation plan for topic count specifications before defaulting to 5.

### Expected Output Format

The generated `test-cases.jsonl` will contain one test case per line:

```json
{"name": "customer-inquiry-1", "input": "How do I reset my password?", "expected_output": "..."}
{"name": "billing-question-1", "input": "What are the pricing plans?", "expected_output": "..."}
```

Each case includes:
- `name`: Unique identifier
- `input`: Test input/query
- `expected_output`: Expected response (if included)
- `metadata`: Optional metadata (category, difficulty, etc.)
