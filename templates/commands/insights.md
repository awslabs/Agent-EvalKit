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
      ```python
      import json
      import pandas as pd
      from pathlib import Path
      from datetime import datetime
      
      def validate_results(results_path: Path) -> dict:
          """Validate that results are from real agent execution."""
          
          # Load results data
          with open(results_path, 'r') as f:
              results = json.load(f)
              
          # Validation checks for real execution
          validation_report = {
              "total_cases": len(results),
              "real_execution": True,
              "issues": []
          }
          
          # Check for simulation indicators
          for i, result in enumerate(results):
              case_id = result.get("test_case_id", f"case_{i}")
              
              # Red flags for simulation
              if "simulated" in str(result).lower():
                  validation_report["real_execution"] = False
                  validation_report["issues"].append(f"{case_id}: Contains 'simulated' keyword")
                  
              # Check for realistic variation in metrics
              if "evaluation" in result:
                  metrics = result["evaluation"]
                  if isinstance(metrics, dict):
                      scores = [m.get("score", 0) for m in metrics.values() if isinstance(m, dict)]
                      if len(set(scores)) == 1 and len(scores) > 1:
                          validation_report["issues"].append(f"{case_id}: Identical scores suggest simulation")
                          
              # Check for realistic execution times
              if "agent_response" in result:
                  exec_time = result["agent_response"].get("execution_time", 0)
                  if exec_time == 0 or exec_time > 300:  # 0 or >5 minutes suspicious
                      validation_report["issues"].append(f"{case_id}: Suspicious execution time: {exec_time}s")
                      
          if validation_report["issues"]:
              print("⚠️  WARNING: Potential simulation detected in results:")
              for issue in validation_report["issues"]:
                  print(f"   - {issue}")
                  
          return validation_report, results
      ```

   b. **Performance Analysis**: Analyze key performance metrics:
      ```python
      def analyze_performance(results: list) -> dict:
          """Analyze agent performance across multiple dimensions."""
          
          analysis = {
              "success_metrics": {},
              "performance_metrics": {},
              "quality_metrics": {},
              "failure_analysis": {}
          }
          
          # Success rate analysis
          successful_cases = [r for r in results if r.get("agent_response", {}).get("status") == "success"]
          analysis["success_metrics"] = {
              "total_cases": len(results),
              "successful_cases": len(successful_cases),
              "success_rate": len(successful_cases) / len(results) if results else 0,
              "failure_rate": (len(results) - len(successful_cases)) / len(results) if results else 0
          }
          
          # Performance metrics (latency, throughput)
          execution_times = [
              r.get("agent_response", {}).get("execution_time", 0) 
              for r in successful_cases
          ]
          
          if execution_times:
              analysis["performance_metrics"] = {
                  "avg_latency": sum(execution_times) / len(execution_times),
                  "min_latency": min(execution_times),
                  "max_latency": max(execution_times),
                  "p95_latency": sorted(execution_times)[int(0.95 * len(execution_times))] if execution_times else 0
              }
          
          # Quality metrics from evaluation results
          quality_scores = []
          for result in successful_cases:
              eval_results = result.get("evaluation", {})
              for metric_name, metric_data in eval_results.items():
                  if isinstance(metric_data, dict) and "score" in metric_data:
                      quality_scores.append({
                          "metric": metric_name,
                          "score": metric_data["score"],
                          "success": metric_data.get("success", False)
                      })
          
          if quality_scores:
              df_quality = pd.DataFrame(quality_scores)
              analysis["quality_metrics"] = {
                  "avg_score": df_quality["score"].mean(),
                  "min_score": df_quality["score"].min(),
                  "max_score": df_quality["score"].max(),
                  "pass_rate": df_quality["success"].mean()
              }
          
          return analysis
      ```

   c. **Pattern Identification**: Identify trends and patterns in results:
      ```python
      def identify_patterns(results: list, analysis: dict) -> dict:
          """Identify patterns in agent performance and failures."""
          
          patterns = {
              "strengths": [],
              "weaknesses": [],
              "failure_modes": [],
              "performance_trends": []
          }
          
          # Analyze failure patterns
          failed_cases = [r for r in results if r.get("agent_response", {}).get("status") != "success"]
          
          if failed_cases:
              # Group failures by error type
              error_types = {}
              for case in failed_cases:
                  error = case.get("agent_response", {}).get("error", "Unknown error")
                  error_type = error.split(":")[0] if ":" in error else error
                  error_types[error_type] = error_types.get(error_type, 0) + 1
              
              patterns["failure_modes"] = [
                  {"error_type": error, "count": count, "percentage": count/len(failed_cases)*100}
                  for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)
              ]
          
          # Identify performance strengths
          if analysis["success_metrics"]["success_rate"] > 0.9:
              patterns["strengths"].append("High success rate (>90%)")
              
          if analysis.get("performance_metrics", {}).get("avg_latency", float('inf')) < 1.0:
              patterns["strengths"].append("Fast response times (<1s average)")
              
          if analysis.get("quality_metrics", {}).get("pass_rate", 0) > 0.8:
              patterns["strengths"].append("High quality scores (>80% pass rate)")
          
          # Identify weaknesses
          if analysis["success_metrics"]["success_rate"] < 0.7:
              patterns["weaknesses"].append("Low success rate (<70%)")
              
          if analysis.get("performance_metrics", {}).get("p95_latency", 0) > 5.0:
              patterns["weaknesses"].append("High P95 latency (>5s)")
              
          if analysis.get("quality_metrics", {}).get("avg_score", 1) < 0.6:
              patterns["weaknesses"].append("Low average quality scores (<0.6)")
          
          return patterns
      ```

   d. **Root Cause Analysis**: Investigate underlying causes of issues:
      ```python
      def perform_root_cause_analysis(results: list, patterns: dict) -> dict:
          """Perform root cause analysis of identified issues."""
          
          root_causes = {
              "performance_issues": [],
              "quality_issues": [],
              "reliability_issues": []
          }
          
          # Analyze performance bottlenecks
          slow_cases = [
              r for r in results 
              if r.get("agent_response", {}).get("execution_time", 0) > 3.0
          ]
          
          if slow_cases:
              # Look for patterns in slow cases
              slow_inputs = [case.get("test_case_id", "unknown") for case in slow_cases]
              root_causes["performance_issues"].append({
                  "issue": "High latency cases detected",
                  "evidence": f"{len(slow_cases)} cases >3s execution time",
                  "affected_cases": slow_inputs[:5],  # Show first 5
                  "recommendation": "Investigate input complexity and processing bottlenecks"
              })
          
          # Analyze quality issues
          low_quality_cases = []
          for result in results:
              eval_results = result.get("evaluation", {})
              avg_score = 0
              score_count = 0
              
              for metric_data in eval_results.values():
                  if isinstance(metric_data, dict) and "score" in metric_data:
                      avg_score += metric_data["score"]
                      score_count += 1
              
              if score_count > 0:
                  avg_score /= score_count
                  if avg_score < 0.5:
                      low_quality_cases.append(result)
          
          if low_quality_cases:
              root_causes["quality_issues"].append({
                  "issue": "Low quality responses detected",
                  "evidence": f"{len(low_quality_cases)} cases with avg score <0.5",
                  "recommendation": "Review agent prompts, training data, or model parameters"
              })
          
          return root_causes
      ```

5. **Improvement Recommendations**: Generate specific, actionable recommendations:

   a. **Prioritized Action Items**: Based on impact and effort:
      ```markdown
      ## Priority 1 - Critical Issues (High Impact, Quick Fixes)
      
      ### Fix High Failure Rate
      **Issue**: Success rate is 65% (target: >90%)
      **Root Cause**: API timeout errors in 23% of cases
      **Action**: Implement retry logic with exponential backoff
      **Expected Impact**: Increase success rate to 85-90%
      **Effort**: 1-2 days
      **Implementation**: Add retry wrapper in agent connector
      
      ## Priority 2 - Performance Improvements (Medium Impact, Medium Effort)
      
      ### Reduce P95 Latency
      **Issue**: P95 latency is 4.2s (target: <2s)
      **Root Cause**: Sequential API calls for complex queries
      **Action**: Implement parallel processing for independent operations
      **Expected Impact**: Reduce P95 latency by 40-50%
      **Effort**: 3-5 days
      **Implementation**: Refactor query processing pipeline
      ```

   b. **Evidence-Based Recommendations**: All recommendations must cite specific data:
      ```markdown
      ### Recommendation: Improve Error Handling
      
      **Evidence**: 
      - 15 cases failed with "Connection timeout" (12% of total)
      - 8 cases failed with "Rate limit exceeded" (6% of total)
      - Average retry attempts: 0 (no retry logic implemented)
      
      **Specific Actions**:
      1. Add exponential backoff retry (3 attempts, 1s/2s/4s delays)
      2. Implement rate limiting detection and queuing
      3. Add circuit breaker for persistent failures
      
      **Expected Outcome**:
      - Reduce timeout failures by 80% (from 15 to ~3 cases)
      - Improve overall success rate from 65% to 85%
      ```

6. **Insights Report Generation**: Create comprehensive report:
   - Executive summary with key findings
   - Detailed performance analysis with charts and metrics
   - Root cause analysis with evidence
   - Prioritized improvement recommendations
   - Implementation roadmap with timelines

7. **Report Structure**:
   ```markdown
   # Agent Evaluation Insights Report
   
   ## Executive Summary
   - Overall Performance: [Rating and key metrics]
   - Critical Issues: [Top 3 issues requiring immediate attention]
   - Strengths: [What the agent does well]
   - Improvement Potential: [Expected gains from recommendations]
   
   ## Performance Analysis
   - Success Rate: [X%] (Target: [Y%])
   - Average Latency: [Xms] (Target: [Yms])
   - Quality Score: [X.X/5.0] (Target: [Y.X])
   - Cost per Query: [$X.XX] (Budget: [$Y.XX])
   
   ## Key Findings
   [Detailed analysis with evidence and data]
   
   ## Improvement Recommendations
   [Prioritized list with implementation details]
   
   ## Next Steps
   [Immediate actions and timeline]
   ```

8. Report completion with insights summary, critical recommendations, and suggested next steps.

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

### Report Quality Checklist

- [ ] All data verified as from real agent execution
- [ ] Performance metrics clearly documented with evidence
- [ ] Root causes identified and supported by data
- [ ] Recommendations are specific and actionable
- [ ] Expected outcomes are quantified
- [ ] Implementation effort is estimated
- [ ] Priorities are based on impact and feasibility
- [ ] Report is accessible to non-technical stakeholders