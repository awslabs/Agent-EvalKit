---
description: Analyze user agent source code and design comprehensive evaluation strategy
scripts:
  sh: scripts/bash/create-new-evaluation.sh --json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.design` in the triggering message **is** the user evaluation requests or agent description. Assume you always have it available in this conversation even if it appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that user evaluation requests or agent description, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and EVAL_SPEC_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for. For single quotes in args like "I'm analyzing", use escape syntax: e.g 'I'\''m analyzing' (or double-quote if possible: "I'm analyzing").

2. Load `templates/spec-template.md` to understand required sections.

3. Follow this execution flow:

    1. Parse user evaluation requests from Input
       If empty: ERROR "No agent description or evaluation requsts provided"
    2. Analyze agent code and capabilities
       Identify: architecture, input/output formats, key functions, tools available
    3. For unclear evaluation aspects:
       - Make informed guesses based on agent type and common evaluation patterns
       - Only mark with [NEEDS CLARIFICATION: specific question] if:
         - The choice significantly impacts evaluation scope or metrics
         - Multiple reasonable evaluation approaches exist with different implications
         - No reasonable default evaluation strategy exists
       - **LIMIT: Maximum 5 [NEEDS CLARIFICATION] markers total**
       - Prioritize clarifications by impact: evaluation scope > metrics > test data > implementation details
    4. Design evaluation strategy and metrics
       If no clear evaluation approach: ERROR "Cannot determine evaluation strategy"
    5. Generate evaluation requirements
       Each requirement must be measurable and testable
       Use reasonable defaults for unspecified details (document assumptions in Assumptions section)
    6. Identify test scenarios and data requirements
    7. Return: SUCCESS (evaluation design ready for planning)

4. Write the evaluation specification to EVAL_SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the agent analysis while preserving section order and headings.

5. **Handle [NEEDS CLARIFICATION] markers** (if any remain):
   1. Extract all [NEEDS CLARIFICATION: ...] markers from the spec
   2. **LIMIT CHECK**: If more than 5 markers exist, keep only the 5 most critical (by evaluation impact) and make informed guesses for the rest
   3. For each clarification needed (max 5), present options to user in this format:
   
      ```markdown
      ## Question [N]: [Topic]
      
      **Context**: [Quote relevant spec section]
      
      **What we need to know**: [Specific question from NEEDS CLARIFICATION marker]
      
      **Suggested Answers**:
      
      | Option | Answer | Implications |
      |--------|--------|--------------|
      | A      | [First suggested answer] | [What this means for the evaluation] |
      | B      | [Second suggested answer] | [What this means for the evaluation] |
      | C      | [Third suggested answer] | [What this means for the evaluation] |
      | Custom | Provide your own answer | [Explain how to provide custom input] |
      
      **Your choice**: _[Wait for user response]_
      ```
   
   4. **CRITICAL - Table Formatting**: Ensure markdown tables are properly formatted with consistent spacing
   5. Number questions sequentially (Q1, Q2, Q3 - max 5 total)
   6. Present all questions together before waiting for responses
   7. Wait for user to respond with their choices for all questions
   8. Update the spec by replacing each [NEEDS CLARIFICATION] marker with the user's answer
   9. If no clarifications needed, proceed directly to step 6

6. Report completion with branch name, evaluation spec file path, and readiness for the next phase (`/evalkit.plan`).

**NOTE:** The script creates and checks out the new branch and initializes the evaluation spec file before writing.

## General Guidelines

### Quick Guidelines

- Focus on **WHAT** to evaluate and **WHY** it matters for the agent.
- Avoid HOW to implement evaluation (no specific frameworks, file structures, code architecture).
- Written for evaluation stakeholders, not just developers.
- DO NOT create any checklists that are embedded in the spec. That will be a separate command.

### Section Requirements

- **Mandatory sections**: Must be completed for every agent evaluation
- **Optional sections**: Include only when relevant to the agent type
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation

When creating this evaluation design from a user prompt:

1. **Make informed guesses**: Use context, agent type patterns, and evaluation best practices to fill gaps
2. **Document assumptions**: Record reasonable defaults in the Assumptions section
3. **Limit clarifications**: Maximum 5 [NEEDS CLARIFICATION] markers - use only for critical decisions that:
   - Significantly impact evaluation scope or approach
   - Have multiple reasonable interpretations with different implications
   - Lack any reasonable default evaluation strategy
4. **Prioritize clarifications**: evaluation scope > metrics selection > test data strategy > implementation details
5. **Think like an evaluator**: Every vague requirement should fail the "measurable and well-defined" checklist item
6. **Common areas needing clarification** (only if no reasonable default exists):
   - Evaluation scope and focus areas (accuracy vs efficiency vs robustness)
   - Metrics selection and measurement methods (when evaluation approach unclear)
   - Test data strategy (when agent domain is highly specialized)
   
**Examples of reasonable defaults** (don't ask about these):

- Evaluation metrics: Standard accuracy, latency, cost metrics for the agent type
- Test data size: Industry-standard sample sizes for the evaluation type
- Evaluation framework: DeepEval or RAGAS for LLM agents unless specified otherwise
- Test scenarios: Standard user flows and edge cases for the agent domain

### Metrics Guidelines

Metrics must be:

1. **Measurable**: Define what will be measured and how
2. **Framework-agnostic**: No mention of specific evaluation tools, libraries, or implementations
3. **Agent-focused**: Describe measurements from agent performance perspective, not system internals
4. **Verifiable**: Can be measured through actual agent execution

**Good examples**:

- "Agent accuracy on test scenarios" with "Manual review of responses"
- "Response time for typical queries" with "Automated timing measurement"
- "Tool selection accuracy" with "Comparison against expected tool choices"
- "Edge case handling" with "Success rate on boundary conditions"

**Bad examples** (implementation-focused):

- "DeepEval metrics show good performance" (tool-specific)
- "Evaluation pipeline runs efficiently" (implementation detail, use agent-facing metric)
- "Test framework validates correctly" (framework-specific)
- "Database queries are optimized" (implementation detail)