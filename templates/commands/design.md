---
description: Analyze user agent source code and design comprehensive evaluation strategy
scripts:
  sh: scripts/bash/create-new-evaluation.sh --json "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.design` in the triggering message **is** the agent description or path to agent code. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that agent description or code path, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and EVAL_SPEC_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for. For single quotes in args like "I'm analyzing", use escape syntax: e.g 'I'\''m analyzing' (or double-quote if possible: "I'm analyzing").

2. Load `templates/eval-template.md` to understand required sections.

3. Follow this execution flow:

    1. Parse agent description/path from Input
       If empty: ERROR "No agent description or path provided"
    2. Analyze agent code and capabilities
       Identify: architecture, input/output formats, key functions, tools available
    3. For unclear evaluation aspects:
       - Make informed guesses based on agent type and common evaluation patterns
       - Only mark with [NEEDS CLARIFICATION: specific question] if:
         - The choice significantly impacts evaluation scope or metrics
         - Multiple reasonable evaluation approaches exist with different implications
         - No reasonable default evaluation strategy exists
       - **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
       - Prioritize clarifications by impact: evaluation scope > metrics > test data > implementation details
    4. Design evaluation strategy and metrics
       If no clear evaluation approach: ERROR "Cannot determine evaluation strategy"
    5. Generate evaluation requirements
       Each requirement must be measurable and testable
       Use reasonable defaults for unspecified details (document assumptions in Assumptions section)
    6. Define success criteria
       Create measurable, framework-agnostic outcomes
       Include both quantitative metrics (accuracy, latency, cost) and qualitative measures (robustness, user experience)
       Each criterion must be verifiable through actual agent execution
    7. Identify test scenarios and data requirements
    8. Return: SUCCESS (evaluation design ready for planning)

4. Write the evaluation specification to EVAL_SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the agent analysis while preserving section order and headings.

5. **Evaluation Design Quality Validation**: After writing the initial spec, validate it against quality criteria:

   a. **Create Evaluation Quality Checklist**: Generate a checklist file at `EVAL_DIR/checklists/evaluation_design.md` using the checklist template structure with these validation items:
   
      ```markdown
      # Evaluation Design Quality Checklist: [AGENT NAME]
      
      **Purpose**: Validate evaluation design completeness and quality before proceeding to implementation
      **Created**: [DATE]
      **Agent**: [Link to evaluation_plan_spec.md]
      
      ## Design Quality
      
      - [ ] No implementation details (specific frameworks, libraries, file structures)
      - [ ] Focused on agent capabilities and evaluation objectives
      - [ ] Written for evaluation stakeholders
      - [ ] All mandatory sections completed
      
      ## Evaluation Completeness
      
      - [ ] No [NEEDS CLARIFICATION] markers remain
      - [ ] Evaluation metrics are measurable and well-defined
      - [ ] Success criteria are quantifiable
      - [ ] Success criteria are framework-agnostic (no implementation details)
      - [ ] All test scenarios are defined
      - [ ] Edge cases and failure modes are identified
      - [ ] Evaluation scope is clearly bounded
      - [ ] Dependencies and assumptions identified
      
      ## Agent Analysis Quality
      
      - [ ] Agent architecture and capabilities clearly documented
      - [ ] Input/output formats specified
      - [ ] Key decision points and reasoning steps identified
      - [ ] Available tools and functions catalogued
      - [ ] Agent limitations and constraints noted
      
      ## Notes
      
      - Items marked incomplete require spec updates before `/evalkit.clarify` or `/evalkit.plan`
      ```
   
   b. **Run Validation Check**: Review the spec against each checklist item:
      - For each item, determine if it passes or fails
      - Document specific issues found (quote relevant spec sections)
   
   c. **Handle Validation Results**:
      
      - **If all items pass**: Mark checklist complete and proceed to step 6
      
      - **If items fail (excluding [NEEDS CLARIFICATION])**:
        1. List the failing items and specific issues
        2. Update the spec to address each issue
        3. Re-run validation until all items pass (max 3 iterations)
        4. If still failing after 3 iterations, document remaining issues in checklist notes and warn user
      
      - **If [NEEDS CLARIFICATION] markers remain**:
        1. Extract all [NEEDS CLARIFICATION: ...] markers from the spec
        2. **LIMIT CHECK**: If more than 3 markers exist, keep only the 3 most critical (by evaluation impact) and make informed guesses for the rest
        3. For each clarification needed (max 3), present options to user in this format:
        
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
        
        4. **CRITICAL - Table Formatting**: Ensure markdown tables are properly formatted:
           - Use consistent spacing with pipes aligned
           - Each cell should have spaces around content: `| Content |` not `|Content|`
           - Header separator must have at least 3 dashes: `|--------|`
           - Test that the table renders correctly in markdown preview
        5. Number questions sequentially (Q1, Q2, Q3 - max 3 total)
        6. Present all questions together before waiting for responses
        7. Wait for user to respond with their choices for all questions (e.g., "Q1: A, Q2: Custom - [details], Q3: B")
        8. Update the spec by replacing each [NEEDS CLARIFICATION] marker with the user's selected or provided answer
        9. Re-run validation after all clarifications are resolved
   
   d. **Update Checklist**: After each validation iteration, update the checklist file with current pass/fail status

6. Report completion with branch name, evaluation spec file path, checklist results, and readiness for the next phase (`/evalkit.clarify` or `/evalkit.plan`).

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
3. **Limit clarifications**: Maximum 3 [NEEDS CLARIFICATION] markers - use only for critical decisions that:
   - Significantly impact evaluation scope or approach
   - Have multiple reasonable interpretations with different implications
   - Lack any reasonable default evaluation strategy
4. **Prioritize clarifications**: evaluation scope > metrics selection > test data strategy > implementation details
5. **Think like an evaluator**: Every vague requirement should fail the "measurable and well-defined" checklist item
6. **Common areas needing clarification** (only if no reasonable default exists):
   - Evaluation scope and focus areas (accuracy vs efficiency vs robustness)
   - Success criteria and thresholds (when business requirements unclear)
   - Test data strategy (when agent domain is highly specialized)
   
**Examples of reasonable defaults** (don't ask about these):

- Evaluation metrics: Standard accuracy, latency, cost metrics for the agent type
- Test data size: Industry-standard sample sizes for the evaluation type
- Success thresholds: Common benchmarks for similar agent types
- Evaluation framework: DeepEval or RAGAS for LLM agents unless specified otherwise
- Test scenarios: Standard user flows and edge cases for the agent domain

### Success Criteria Guidelines

Success criteria must be:

1. **Measurable**: Include specific metrics (accuracy %, latency ms, cost $, success rate %)
2. **Framework-agnostic**: No mention of specific evaluation tools, libraries, or implementations
3. **Agent-focused**: Describe outcomes from agent performance perspective, not system internals
4. **Verifiable**: Can be tested/validated through actual agent execution

**Good examples**:

- "Agent achieves 95% accuracy on test scenarios"
- "Average response time under 500ms for typical queries"
- "Tool selection accuracy above 90%"
- "Handles edge cases gracefully with <5% failure rate"

**Bad examples** (implementation-focused):

- "DeepEval metrics show good performance" (tool-specific)
- "Evaluation pipeline runs efficiently" (implementation detail, use agent-facing metric)
- "Test framework validates correctly" (framework-specific)
- "Database queries are optimized" (implementation detail)