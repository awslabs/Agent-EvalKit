---
description: Analyze the evaluation execution results and propose improvement suggestions
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.insights` in the triggering message **is** additional context or specific analysis requirements. This command analyzes evaluation execution results and provides actionable improvement suggestions.

Given that context, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and RESULTS_PATH. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

2. Load and analyze the evaluation results from the specified path.

3. Follow this execution flow:

    1. Parse user context from Input (if provided)
    2. Load and validate evaluation results data
    3. Perform comprehensive results analysis
    4. Identify patterns, strengths, and weaknesses
    5. Generate actionable improvement recommendations
    6. Create detailed insights report with evidence
    7. Provide prioritized action items for agent enhancement

4. **Results Analysis Process**:

   a. **Data Validation and Loading**: Ensure results are from real execution:
      - Load evaluation results from the specified path
      - Validate that results come from actual agent execution (not simulation)
      - Check for red flags: identical metrics, unrealistic execution times, simulation keywords
      - Verify data completeness and format consistency

   b. **Performance Analysis**: Analyze key performance metrics:
      - **Success Rate**: Calculate overall success/failure rates
      - **Latency Metrics**: Average, P95, min/max response times
      - **Quality Scores**: Evaluation metric performance across test cases
      - **Throughput**: Cases processed per unit time
      - **Cost Analysis**: Resource usage and efficiency metrics

   c. **Pattern Identification**: Identify trends and patterns in results:
      - **Failure Modes**: Common error types and their frequency
      - **Performance Trends**: Patterns in latency and quality over time
      - **Strengths**: Areas where agent performs exceptionally well
      - **Weaknesses**: Consistent problem areas requiring attention

   d. **Root Cause Analysis**: Investigate underlying causes of issues:
      - **Performance Bottlenecks**: Identify what causes slow responses
      - **Quality Issues**: Understand why certain metrics underperform
      - **Reliability Problems**: Analyze failure patterns and triggers
      - **Resource Constraints**: Identify limiting factors

5. **Improvement Recommendations**: Generate specific, actionable recommendations:

   a. **Prioritized Action Items**: Based on impact and feasibility:
      
      **Priority 1 - Critical Issues (High Impact, Immediate Attention)**
      - **High Failure Rate**: If success rate <70%, identify primary failure modes
      - **Performance Bottlenecks**: If P95 latency >5s, analyze slow cases
      - **Quality Issues**: If evaluation scores <0.6, examine response quality
      
      **Priority 2 - Performance Improvements (Medium Impact, Optimization)**
      - **Latency Optimization**: Reduce average response time
      - **Cost Efficiency**: Optimize resource usage and API calls
      - **Throughput Enhancement**: Improve processing capacity
      
      **Priority 3 - Enhancement Opportunities (Lower Impact, Future Improvements)**
      - **Edge Case Handling**: Address uncommon failure scenarios
      - **User Experience**: Improve response formatting and clarity
      - **Monitoring**: Add better observability and tracking

   b. **Evidence-Based Recommendations**: All recommendations must cite specific data:
      
      **Recommendation Structure**:
      - **Issue**: Clear problem statement with metrics
      - **Evidence**: Specific data points from evaluation results
      - **Root Cause**: Analysis of underlying causes
      - **Recommended Actions**: Specific improvement suggestions
      - **Expected Impact**: Quantified improvement predictions
      - **Success Metrics**: How to measure improvement

6. **Insights Report Generation**: Create focused report with:
   - Executive summary with key findings
   - Performance analysis with core metrics
   - Prioritized improvement recommendations with evidence
   - Success metrics for tracking progress

7. **Report Structure**:
   ```markdown
   # Agent Evaluation Insights Report
   
   ## Executive Summary
   - Overall Performance: [Rating and key metrics]
   - Critical Issues: [Top issues requiring attention]
   - Key Strengths: [What works well]
   
   ## Performance Analysis
   - Success Rate: [X%]
   - Average Latency: [Xms]
   - Quality Score: [X.X/5.0]
   - Cost per Query: [$X.XX]
   
   ## Improvement Recommendations
   [Prioritized list with evidence and expected impact]
   
   ## Success Metrics
   [How to measure improvement progress]
   ```

8. Report completion with insights summary and critical recommendations.

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
- Execution times of exactly 0 or unrealistic values
- Keywords like "simulated", "mocked", "fake" in results
- Lack of natural variation in performance metrics

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

Ensure your insights report:
- Uses data from real agent execution (never simulation)
- Provides specific, actionable recommendations with evidence
- Quantifies expected improvements and success metrics
- Prioritizes recommendations by impact and feasibility