# Agent Evaluation Report for QA+Search Agent

## Executive Summary

- **Test Scale**: 2 test cases covering general information queries and current events queries
- **Success Rate**: 100% (all test cases passed both metrics)
- **Status**: Good - Strong relevancy but factual accuracy needs improvement
- **Strengths**:
  - Perfect answer relevancy (100% score across all tests)
  - Comprehensive responses with good structure
  - Effective use of search results to inform answers
- **Critical Issues**:
  - Fabricated specific dates not present in search results (e.g., "November 19, 2025")
  - Incorrect financial figures ($22.4B vs actual $6.5B for CoreWeave deal)
  - Made-up product names and technical details not in source material
- **Action Priority**:
  - Critical: Implement fact-checking layer to prevent hallucination of specific dates/numbers
  - Important: Add source attribution to make grounding more explicit
  - Enhancement: Improve answer generation prompts to emphasize faithfulness

---

## Evaluation Results

### Test Case Coverage

- **General Information Queries**: Questions requiring factual information from web searches about latest AI developments. Tests basic search and synthesis capabilities with straightforward queries.
- **Current Events Queries**: Time-sensitive questions about recent news and events. Tests ability to retrieve and synthesize current information.

### Results

| **Metric**           | **Score** | **Target** | **Status** |
| :------------------- | :-------- | :--------- | :--------- |
| Faithfulness         | 78.2%     | 70%+       | ✅ Pass     |
| Answer Relevancy     | 100.0%    | 70%+       | ✅ Pass     |
| Overall Pass Rate    | 100%      | 70%+       | ✅ Pass     |

### Results Summary

The QA+Search agent demonstrates excellent query understanding and answer relevancy, achieving perfect scores across all test cases. However, faithfulness scores reveal a concerning pattern: while responses stay topically relevant, they frequently include fabricated specifics like dates, monetary amounts, and technical details not present in the retrieved search results. The average faithfulness score of 78.2% indicates the agent is grounding most content in sources but consistently adding unsupported embellishments.

---

## Agent Success Analysis

### Strengths

- **Perfect Query Understanding**: Agent achieves 100% answer relevancy across all test cases
- **Evidence**: Both test cases scored 1.0 for relevancy, with evaluation noting "perfectly addresses the question" and "no irrelevant content detected"
- **Contributing Factors**: Effective use of Strands Agent framework with Bedrock Claude Sonnet enables strong semantic understanding of user intent

- **Comprehensive Information Synthesis**: Agent successfully aggregates information from multiple search results into well-structured, detailed responses
- **Evidence**: Responses averaged 17-18 retrieval context sources, all integrated into coherent multi-section answers
- **Contributing Factors**: Tavily search API provides rich, relevant sources; agent's synthesis capabilities organize disparate information effectively

- **Structured Response Format**: Responses use clear hierarchical organization with headers, bullet points, and categories
- **Evidence**: Both responses featured organized sections (Major Releases, Trends, Partnerships, etc.) making information easy to scan
- **Contributing Factors**: Claude Sonnet's strong instruction-following and formatting capabilities

### High-Performing Scenarios

- **Broad Topic Queries**: Agent excels at "what are the latest developments" style questions requiring synthesis of multiple sources
- **Key Characteristics**: Questions benefiting from comprehensive overviews rather than specific fact-checking perform best

---

## Agent Failure Analysis

### Issue 1 - Critical: Hallucination of Specific Dates and Numbers

- **Issue**: Agent fabricates specific dates (e.g., "November 19, 2025") and financial figures ($22.4B vs $6.5B) not present in search results
- **Root Cause**: qa_agent/qa_agent.py:47-52 - No explicit grounding constraints in agent configuration; Claude Sonnet's tendency to provide specific details leads to plausible-sounding but fabricated specifics when search results contain partial information
- **Evidence**:
  - Test Case 1: Fabricated "$6.2 billion" for Project Prometheus (faithfulness score: 0.83)
  - Test Case 2: Multiple date fabrications (Nov 18-20, 2025) and wrong financial figures ($22.4B instead of $6.5B for CoreWeave), incorrect product name "Gemini 3" instead of "Gemini" (faithfulness score: 0.73)
- **Impact**: Reduces faithfulness scores by 17-27 points; undermines trust in factual accuracy; creates risk of spreading misinformation
- **Priority Fixes**:
  - P1 - Add Fact-Checking Layer: Implement post-generation verification that checks claims against retrieval context → Expected gain: Faithfulness +15-20 points
  - P2 - Update System Prompt: Add explicit instruction to avoid specifics not in sources, use qualifiers like "according to sources" → Expected gain: Faithfulness +10 points
  - P3 - Source Attribution: Modify response generation to cite specific search results for factual claims → Expected gain: Faithfulness +5-10 points

### Issue 2 - Medium: Missing Source Transparency

- **Issue**: Responses don't explicitly indicate which facts come from which sources, making verification difficult
- **Root Cause**: qa_agent/qa_agent.py:15-44 - Tool returns search results but agent doesn't preserve source attribution in final output
- **Evidence**: Neither test case response included source citations or links despite having 17-18 sources available
- **Impact**: Users cannot verify claims; reduces transparency; makes it harder to assess credibility of different facts
- **Priority Fixes**:
  - P1 - Add Source Markers: Modify web_search tool response to include source IDs, update agent prompt to reference sources → Expected gain: Transparency +30 points, Trust +15 points
  - P2 - Inline Citations: Format responses to include [1], [2] style citations linked to source list → Expected gain: Verifiability +25 points

---

## Action Items & Recommendations

### Implement Faithfulness Safeguards - Priority 1 (Critical)

- **Description**: Add multiple layers of protection against hallucination to improve factual accuracy from 78% to 90%+
- **Actions**:
  - [ ] Update agent system prompt in qa_agent.py to explicitly instruct: "Only include specific details (dates, numbers, names) if they appear verbatim in search results. Use qualifiers like 'sources report' or 'according to available information' for uncertain details."
  - [ ] Implement post-generation fact-checking: Create a validation step that extracts factual claims (dates, numbers, names) and verifies each appears in retrieval context
  - [ ] Add confidence scoring: Tag each factual claim with confidence based on how explicitly it appears in sources
  - [ ] Test with current test cases and verify faithfulness improves to 90%+

### Add Source Attribution System - Priority 2 (Critical)

- **Description**: Make grounding explicit by adding source citations to all factual claims
- **Actions**:
  - [ ] Modify web_search tool in qa_agent.py:15-44 to assign unique IDs to each search result (e.g., [1], [2], [3])
  - [ ] Update agent prompt to require inline citations: "For each factual claim, add a source reference like [1] [2]"
  - [ ] Add source list at end of response: "Sources: [1] Title (URL)"
  - [ ] Verify test case responses now include citations for all major facts

### Enhance Test Coverage - Priority 3 (Enhancement)

- **Description**: Expand test cases to cover edge cases and specific failure modes
- **Actions**:
  - [ ] Add test cases with conflicting information in search results to test disambiguation
  - [ ] Include queries requiring specific numerical facts to stress-test hallucination prevention
  - [ ] Add cases with limited/ambiguous search results to test graceful degradation
  - [ ] Create test cases requiring temporal reasoning (e.g., "what changed since...")

### Improve Evaluation Metrics - Priority 4 (Enhancement)

- **Description**: Add more granular metrics to catch specific types of errors
- **Actions**:
  - [ ] Implement named entity extraction metric to specifically measure hallucination of dates, numbers, names
  - [ ] Add citation quality metric: percentage of facts with proper source attribution
  - [ ] Create temporal accuracy metric: verify dates/timeframes match sources
  - [ ] Measure response precision: ratio of verifiable claims to total claims

---

## Artifacts & Reproduction

### Reference Materials

- **Agent Code**: qa_agent/qa_agent.py
- **Test Cases**: eval/test-cases.jsonl
- **Traces**: eval/traces/ (2 trace files)
- **Results**: eval/results/evaluation_results_20251120_214918.json
- **Evaluation Code**: eval/metrics.py, eval/run_evaluation.py

### Reproduction Steps

1. Ensure AWS credentials configured for Bedrock access
2. Run: `source .venv/bin/activate`
3. Execute agent: `python eval/agent_runner.py --input eval/test-cases.jsonl`
4. Process traces: `python .evalkit/tracing/trace-processor.py --input eval/otel-traces.jsonl --output-dir eval/traces/`
5. Run evaluation: `python eval/run_evaluation.py --input eval/traces/ --output eval/results/`

---

## Evaluation Limitations and Improvement

### Test Data Improvement

- **Current Limitations**:
  - Only 2 test cases - insufficient for statistical significance
  - Both test cases are similar in nature (broad "latest developments" queries)
  - No edge cases or adversarial examples
  - Test cases don't specifically target known weaknesses (dates, numbers, conflicting info)
- **Recommended Improvements**:
  - Expand to 10-15 test cases covering diverse query types
  - Add specific test cases for date verification, numerical accuracy, and conflicting information handling
  - Include queries with sparse or ambiguous search results
  - Add negative test cases (queries where agent should admit uncertainty)

### Evaluation Code Enhancement

- **Current Limitations**:
  - Faithfulness metric catches overall hallucination but not specific error types
  - No metrics for citation quality or source attribution
  - Evaluation doesn't quantify severity of different types of errors (wrong date vs wrong sentiment)
  - No automated breakdown of which specific facts are hallucinated
- **Recommended Improvements**:
  - Implement granular metrics for dates, numbers, and named entities
  - Add citation coverage metric (% of claims with sources)
  - Create error taxonomy: categorize hallucinations by type and severity
  - Build automated fact extraction and verification pipeline

### Evaluation Process Improvement

- **Current Limitations**:
  - Manual trace analysis required to understand failure modes
  - No automated root cause analysis
  - Results don't link back to specific agent code paths
  - No longitudinal tracking of improvements over time
- **Recommended Improvements**:
  - Implement automated failure pattern detection
  - Add code-level tracing to link errors to specific agent logic
  - Create dashboard for tracking metric trends across evaluations
  - Build regression detection: flag when scores decrease on previously-passing cases
