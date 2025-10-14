---
description: Clarify underspecified areas in evaluation design by asking up to 5 highly targeted clarification questions and encoding answers back into the spec (recommended before /evalkit.plan)
scripts:
  sh: scripts/bash/check-prerequisites.sh --json -paths-only
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.clarify` in the triggering message **is** additional context or specific areas to clarify. This command helps refine the evaluation design by addressing ambiguous or underspecified areas.

Given that context, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and EVAL_SPEC_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

2. Load the current evaluation specification from EVAL_SPEC_FILE to understand the current state.

3. Follow this execution flow:

    1. Parse user context from Input (if provided)
    2. Analyze current evaluation specification for:
       - Remaining [NEEDS CLARIFICATION] markers
       - Vague or ambiguous evaluation requirements
       - Missing success criteria or thresholds
       - Unclear test scenarios or data requirements
       - Ambiguous evaluation scope or focus areas
    3. Identify clarification priorities:
       - **Critical**: Affects evaluation scope, metrics selection, or success criteria
       - **Important**: Affects test data strategy or evaluation approach
       - **Minor**: Affects implementation details or edge cases
    4. Generate targeted clarification questions
    5. Present questions to user and collect responses
    6. Update evaluation specification with clarified requirements
    7. Validate updated specification for completeness

4. **Clarification Process**:

   a. **Identify Clarification Needs**: Scan the evaluation specification for:
      - Explicit [NEEDS CLARIFICATION] markers
      - Vague success criteria (e.g., "good performance", "acceptable accuracy")
      - Unclear evaluation scope (e.g., "comprehensive testing")
      - Ambiguous test scenarios (e.g., "typical use cases")
      - Missing thresholds or benchmarks

   b. **Prioritize Questions**: Focus on the most impactful clarifications first:
      1. Evaluation scope and focus areas
      2. Success criteria and performance thresholds
      3. Test data strategy and coverage
      4. Evaluation metrics and measurement approach
      5. Edge cases and failure scenarios

   c. **Present Clarification Questions**: For each identified area, present structured questions:

      ```markdown
      ## Clarification [N]: [Area/Topic]
      
      **Current State**: [Quote from current spec showing ambiguity]
      
      **What needs clarification**: [Specific question]
      
      **Options**:
      
      | Option | Approach | Impact on Evaluation |
      |--------|----------|---------------------|
      | A      | [First option] | [How this affects the evaluation] |
      | B      | [Second option] | [How this affects the evaluation] |
      | C      | [Third option] | [How this affects the evaluation] |
      | Custom | [Your specific input] | [How custom input would be used] |
      
      **Recommendation**: [Your recommended option with brief rationale]
      
      **Your choice**: _[Wait for user response]_
      ```

   d. **Collect and Apply Responses**: 
      - Wait for user to respond to all questions
      - Update the evaluation specification with the clarified requirements
      - Replace [NEEDS CLARIFICATION] markers with specific, actionable requirements
      - Add any new assumptions to the Assumptions section

   e. **Validate Updated Specification**:
      - Ensure all clarifications are properly integrated
      - Check that success criteria are now measurable and specific
      - Verify that evaluation scope is clearly defined
      - Confirm that test scenarios are concrete and actionable

5. **Update Quality Checklist**: After clarifications are applied:
   - Update the evaluation design quality checklist
   - Mark resolved items as complete
   - Note any remaining areas that may need attention

6. Report completion with updated evaluation specification path, summary of clarifications made, and readiness for the next phase (`/evalkit.plan`).

## General Guidelines

### Clarification Principles

- **Focus on Impact**: Prioritize clarifications that most affect evaluation outcomes
- **Be Specific**: Ask for concrete, measurable requirements rather than general preferences
- **Provide Context**: Explain why each clarification matters for the evaluation
- **Offer Options**: Give users clear choices rather than open-ended questions
- **Document Decisions**: Record the rationale behind clarification choices

### Question Quality Standards

Good clarification questions:
- Address specific ambiguities in the current specification
- Provide clear options with different implications
- Focus on evaluation outcomes rather than implementation details
- Include recommendations based on best practices
- Are answerable by stakeholders without deep technical knowledge

Poor clarification questions:
- Ask about implementation details (frameworks, file structures)
- Are too broad or philosophical
- Don't provide clear options or guidance
- Focus on technical rather than evaluation concerns
- Require specialized knowledge to answer

### Success Criteria Clarification

When clarifying success criteria, ensure they become:

1. **Quantitative**: Include specific numbers, percentages, or thresholds
2. **Measurable**: Can be automatically computed from evaluation results
3. **Relevant**: Directly relate to agent performance and user value
4. **Achievable**: Realistic given the agent's intended capabilities
5. **Time-bound**: Include performance expectations (e.g., response time)

**Before clarification** (vague):
- "Agent should perform well on typical queries"
- "Good accuracy is expected"
- "Response time should be reasonable"

**After clarification** (specific):
- "Agent achieves >90% accuracy on customer service queries"
- "95% of responses are factually correct and relevant"
- "Average response time <2 seconds for standard queries"

### Test Scenario Clarification

When clarifying test scenarios, ensure they become:

1. **Concrete**: Specific examples rather than general categories
2. **Representative**: Cover the agent's intended use cases
3. **Measurable**: Have clear success/failure criteria
4. **Comprehensive**: Include both typical and edge cases
5. **Realistic**: Reflect actual usage patterns

**Before clarification** (vague):
- "Test with various user inputs"
- "Include edge cases"
- "Cover typical scenarios"

**After clarification** (specific):
- "Test 100 customer service queries across 5 categories: billing, technical support, returns, account management, product information"
- "Include 20 edge cases: ambiguous queries, multi-part questions, requests outside agent scope"
- "Test with both new and returning customer scenarios"
