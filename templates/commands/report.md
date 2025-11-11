---
description: Analyze results and provide improvement recommendations
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-results
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.report` in the triggering message **is** additional context or specific analysis requirements. This command analyzes evaluation execution results and provides actionable improvement recommendations.

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

2. Run the script `{SCRIPT}` and parse its JSON output for BRANCH_NAME and RESULTS_PATH. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

3. Load and analyze the evaluation results from the specified path.

4. Follow this execution flow:

    1. Parse user context from Input (if provided)
    2. Load and validate evaluation results data
    3. Perform comprehensive results analysis
    4. Identify patterns, strengths, and weaknesses
    5. Generate actionable improvement recommendations
    6. Create detailed advisory report with evidence
    7. Provide prioritized action items for agent enhancement

5. **Results Analysis Process**:

   a. **Data Validation**: Ensure results are from real execution:
      - Load evaluation results from the specified path
      - Validate that results come from actual agent execution (not simulation)
      - Verify data completeness and format consistency

   b. **Results Analysis**: Analyze evaluation outcomes:
      - **Success Rate**: Calculate overall success/failure rates
      - **Quality Scores**: Evaluation metric performance across test cases
      - **Failure Patterns**: Common error types and their frequency
      - **Strengths & Weaknesses**: Areas of strong vs. poor performance

   c. **Insights Generation**: Identify key findings:
      - **Root Causes**: Why certain metrics underperform
      - **Improvement Opportunities**: Specific areas for enhancement
      - **Quality Trends**: Patterns in evaluation scores and response quality

6. **Improvement Recommendations**: Generate specific, actionable recommendations:

   a. **Prioritized Recommendations**: Based on evaluation findings:
      
      **Critical Issues** (Immediate attention required)
      - Address high failure rates or low quality scores
      - Fix systematic errors in reasoning or response generation
      
      **Quality Improvements** (Medium-term enhancements)
      - Improve consistency across test cases
      - Enhance response completeness and accuracy
      
      **Enhancement Opportunities** (Future improvements)
      - Handle edge cases more effectively
      - Improve response clarity and formatting

   b. **Evidence-Based Recommendations**: All recommendations must cite specific data:
      - **Issue**: Clear problem statement with evaluation metrics
      - **Evidence**: Specific data points from results
      - **Recommended Actions**: Specific improvement suggestions
      - **Expected Impact**: Predicted improvements in evaluation scores

7. **Advisory Report Generation**: Create focused report with:
   - Executive summary with key findings
   - Evaluation results analysis
   - Prioritized improvement recommendations with evidence

8. **Report Structure**:
   ```markdown
   # Agent Evaluation Report
   
   ## Executive Summary
   - Overall Performance: [Key evaluation metrics]
   - Critical Issues: [Top issues requiring attention]
   - Key Strengths: [What works well]
   
   ## Evaluation Results
   - Success Rate: [X%]
   - Quality Scores: [Metric breakdown]
   - Key Patterns: [Notable findings]
   
   ## Improvement Recommendations
   [Prioritized list with evidence and expected impact]
   ```

9. Report completion with actionable insights and recommendations.

## General Guidelines

### Analysis Principles

- **Evidence-Based**: All insights must be supported by actual execution data
- **Actionable**: Recommendations must be specific and implementable
- **Prioritized**: Focus on high-impact improvements first
- **Measurable**: Include expected outcomes and success metrics
- **Realistic**: Consider implementation effort and constraints

### Red Flags for Simulation

Always check for these indicators of simulated results:
- Identical metrics across different test cases
- Perfect success rates (100%) with large test sets
- Keywords like "simulated", "mocked", "fake" in results
- Lack of natural variation in evaluation scores

### Quality Standards for Recommendations

**Good Recommendations**:
- Cite specific evidence from results
- Include expected impact and effort estimates
- Provide concrete implementation steps
- Address root causes, not just symptoms
- Are feasible given current constraints

**Poor Recommendations**:
- Make vague suggestions without evidence
- Don't quantify expected improvements
- Focus on symptoms rather than causes
- Are too generic or theoretical
- Ignore practical implementation challenges

### Report Quality Standards

Ensure your advisory report:
- Uses data from real agent execution (never simulation)
- Provides specific, actionable recommendations with evidence
- Focuses on evaluation results analysis and insights
- Prioritizes recommendations by impact on evaluation performance