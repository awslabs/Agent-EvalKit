---
description: Execute core evaluation pipeline implementation according to the established plan
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-design --require-tracing --require-test-cases --include-design
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.implement` in the triggering message **is** additional context or specific implementation requirements. This command executes the core evaluation pipeline implementation, assuming tracing and test cases are already prepared.

Given that context, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and IMPLEMENTATION_STATUS. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

2. Load the current evaluation design (`eval/eval-design.md`) to understand the task structure and requirements.

3. Follow this execution flow:

    1. Parse user context from Input (if provided)
    2. Review evaluation design and validate prerequisites
    3. Verify tracing setup and test case availability
    4. Execute core evaluation pipeline implementation:
       - Setup Project Structure (always required)
       - **Trace Extraction Layer (critical first step - always required)**
       - Core Evaluation Pipeline Module (always required, using extracted trace data)
       - Results & Analysis (always required)
       - Code Review & Testing (always required)
    5. Test and validate each component as it's built
    6. Ensure all evaluation uses actual agent execution, no mocking

## Implementation Process

### Task Execution Strategy

Follow the established design structure systematically:
- **Prerequisites**: Ensure tracing is enabled and test cases are available
- **Core Focus**: Implement evaluation pipeline, metrics, and analysis only

### Prerequisites Validation

Before implementation, verify:
- `eval/eval-design.md` exists and contains complete specifications
- **Trace Data Availability**: Evaluation input data is accessible
  - **Option A - Existing Traces**: Pre-existing trace files (`eval/tracing/otel-traces.jsonl` or similar)
  - **Option B - Live Tracing**: Agent is instrumented and traces can be collected
    - OTEL collector is configured (`eval/tracing/otel-config.yaml`)
    - Agent has tracing enabled (via `/evalkit.trace` command)
    - Test trace collection works (`eval/tracing/otel-traces.jsonl` can be generated)
- **Test Cases**: Comprehensive test cases are available (if needed for trace generation)
  - Test cases file exists (`eval/test-cases.jsonl`) OR existing traces contain sufficient test scenarios
  - Test cases cover all evaluation areas (via `/evalkit.data` command) OR traces represent desired evaluation scope
  - Test case format is valid and complete OR trace extraction can derive test scenarios

### Python Environment & Dependency Management

**Strategy**: Set up environment first to support both agent execution and evaluation framework dependencies.

#### Environment Setup Process (First Step)

1. **Detect Existing Dependencies**: Check for existing dependency files in agent directory and repository root
   ```bash
   # Check for existing dependency files (in order of priority)
   find . -name "requirements.txt" -o -name "pyproject.toml" -o -name "setup.py" -o -name "Pipfile" -o -name "environment.yml"
   ```

2. **Consolidate Requirements**: Create unified `requirements.txt` at repository root
   ```bash
   # Merge agent dependencies with evaluation framework dependencies
   # Include agent's existing requirements if found
   # Add evaluation framework dependencies
   ```

3. **Create Virtual Environment**: Use `uv` to create `.venv` at repository root
   ```bash
   # Create virtual environment at repository root (not in eval/ directory)
   uv venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or .venv\Scripts\activate  # Windows
   ```

4. **Install Dependencies**: Use `uv pip install` for consistent dependency resolution
   ```bash
   uv pip install -r requirements.txt
   ```

#### Dependency Detection Priority

Check for existing dependency files in this order:
- `requirements.txt` (standard Python)
- `pyproject.toml` (modern Python projects)
- `setup.py` (legacy Python packages)
- `Pipfile` (pipenv projects)
- `environment.yml` (conda environments)

#### Evaluation Framework Dependencies

Add these to consolidated `requirements.txt`:
```txt
# Core evaluation dependencies
boto3>=1.35.0
deepeval>=0.21.0
traceloop-sdk>=0.0.75
opentelemetry-sdk>=1.26.0
opentelemetry-exporter-otlp>=1.26.0
pydantic>=2.0.0
pyyaml>=6.0
jsonlines>=3.0.0
```

### Leveraging Context7 MCP for Latest Library Information

**IMPORTANT**: EvalKit projects include Context7 MCP server for accessing the latest documentation and usage patterns. Use this built-in capability to ensure you're implementing with current best practices:

- **Before implementing evaluation libraries**: Ask Context7 for the latest usage patterns, API changes, and best practices for libraries like Traceloop, DeepEval, LiteLLM, or other open source frameworks
- **For dependency management**: Get current version recommendations and compatibility information
- **For integration patterns**: Access up-to-date examples and implementation guides
- **For troubleshooting**: Get current solutions for common integration issues

Example Context7 queries:
- "What's the latest DeepEval API for custom metrics?"
- "Show me current best practices for Traceloop"
- "How to properly configure evaluation environments with current dependency versions?"

This ensures your implementation uses the most current approaches and avoids deprecated patterns.

## Implementation Principles

**CRITICAL: Always Create Minimal Working Version**: Implement the most basic version that works

**Core Implementation Guidelines**:
- **Follow the Design**: Implement according to the established design structure
- **Trace-First Evaluation**: Prioritize trace-based evaluation over direct agent integration
- **Use Context7 MCP**: Leverage built-in Context7 MCP server for latest library documentation and best practices
- **Configuration-Driven**: Use `config.yaml` for all settings
- **Error Resilience**: Handle failures gracefully with clear error messages

## Trace-Based Evaluation Architecture

**CRITICAL PRINCIPLE**: The core evaluation module should be **decoupled** from direct agent execution and work with OTEL traces as the primary input source.
### Architecture Flow: `agent execution → otel-json traces → extraction → evaluation`

This decoupled architecture provides:
- **Flexibility**: Evaluate agents without source code access
- **Scalability**: Process large trace datasets offline
- **Reliability**: Evaluation doesn't depend on agent availability
- **Reproducibility**: Consistent results from stored traces

### Standard Trace Normalization Utilities

**CRITICAL**: Always implement these standard utility functions to ensure consistent OTLP-JSON trace processing across all evaluation code.

#### Core Trace Processing Functions

Create `eval/trace_extractor.py` with these standard utilities:

```python
"""
Standard OTLP-JSON trace normalization utilities for consistent evaluation processing.
Implements single-phase normalization: OTLP-JSON → NormalizedTrace data class.
"""
import json
import jsonlines
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

@dataclass
class NormalizedSpan:
    """Standardized span structure extracted from OTLP format"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    kind: int
    start_time: int  # nanoseconds
    end_time: int    # nanoseconds
    duration_ns: int
    attributes: Dict[str, Any]
    resource_attributes: Dict[str, str]
    scope: str
    status: Dict[str, Any]

@dataclass
class TraceMetadata:
    """Computed metadata for a complete trace"""
    service_name: str
    total_duration_ns: int
    span_count: int
    start_time: int
    end_time: int

@dataclass
class NormalizedTrace:
    """Complete normalized trace with helper methods for dynamic extraction"""
    trace_id: str
    spans: List[NormalizedSpan]
    metadata: TraceMetadata
    
    def find_spans(self,
                   name_contains: Optional[str] = None,
                   scope_contains: Optional[str] = None,
                   attribute_filter: Optional[Dict[str, Any]] = None,
                   custom_filter: Optional[callable] = None) -> List[NormalizedSpan]:
        """Find spans matching specified criteria"""
        filtered_spans = self.spans
        
        if name_contains:
            filtered_spans = [s for s in filtered_spans if name_contains.lower() in s.name.lower()]
        
        if scope_contains:
            filtered_spans = [s for s in filtered_spans if scope_contains.lower() in s.scope.lower()]
        
        if attribute_filter:
            for key, value in attribute_filter.items():
                filtered_spans = [s for s in filtered_spans if s.attributes.get(key) == value]
        
        if custom_filter:
            filtered_spans = [s for s in filtered_spans if custom_filter(s)]
        
        return filtered_spans
    
    def extract_attributes(self, attribute_names: List[str], spans: Optional[List[NormalizedSpan]] = None) -> List[Dict[str, Any]]:
        """Extract specified attributes from spans"""
        target_spans = spans if spans is not None else self.spans
        
        results = []
        for span in target_spans:
            span_data = {
                "span_name": span.name,
                "duration_ms": span.duration_ns / 1_000_000
            }
            for attr_name in attribute_names:
                span_data[attr_name] = span.attributes.get(attr_name)
            results.append(span_data)
        
        return results
    
    def get_execution_flow(self) -> List[NormalizedSpan]:
        """Get spans sorted by execution order (start time)"""
        return sorted(self.spans, key=lambda s: s.start_time)
    
    def has_errors(self) -> bool:
        """Check if trace contains any error spans"""
        return any(span.status.get("code") == 2 for span in self.spans)
    
    def get_error_spans(self) -> List[NormalizedSpan]:
        """Get all spans with error status"""
        return [span for span in self.spans if span.status.get("code") == 2]

class TraceExtractor:
    """Standard utilities for OTLP-JSON trace normalization"""
    
    def __init__(self, traces_path: str = "eval/tracing/otel-traces.jsonl"):
        self.traces_path = Path(traces_path)
    
    def load_and_normalize_traces(self) -> Dict[str, NormalizedTrace]:
        """Load OTLP-JSON traces and normalize to NormalizedTrace objects"""
        raw_spans = self._load_otlp_spans()
        normalized_spans = [self._extract_span_from_otlp(span) for span in raw_spans]
        return self._group_spans_by_trace_id(normalized_spans)
    
    def _load_otlp_spans(self) -> List[Dict]:
        """Load raw OTLP-JSON spans from jsonl file"""
        spans = []
        with jsonlines.open(self.traces_path) as reader:
            for line in reader:
                # Extract spans from nested OTLP structure
                for resource_span in line.get("resourceSpans", []):
                    for scope_span in resource_span.get("scopeSpans", []):
                        for span in scope_span.get("spans", []):
                            # Attach resource and scope metadata
                            span["_resource"] = resource_span.get("resource", {})
                            span["_scope"] = scope_span.get("scope", {})
                            spans.append(span)
        return spans
    
    def _extract_span_from_otlp(self, otlp_span: Dict) -> NormalizedSpan:
        """Extract NormalizedSpan from nested OTLP format"""
        # Convert OTLP attributes to simple dict
        attributes = {}
        for attr in otlp_span.get("attributes", []):
            key = attr["key"]
            value_obj = attr["value"]
            # Extract value based on type
            if "stringValue" in value_obj:
                attributes[key] = value_obj["stringValue"]
            elif "intValue" in value_obj:
                attributes[key] = int(value_obj["intValue"])
            elif "doubleValue" in value_obj:
                attributes[key] = float(value_obj["doubleValue"])
            elif "boolValue" in value_obj:
                attributes[key] = value_obj["boolValue"]
        
        # Extract resource attributes
        resource_attrs = {}
        for attr in otlp_span.get("_resource", {}).get("attributes", []):
            key = attr["key"]
            value_obj = attr["value"]
            if "stringValue" in value_obj:
                resource_attrs[key] = value_obj["stringValue"]
        
        return NormalizedSpan(
            trace_id=otlp_span.get("traceId"),
            span_id=otlp_span.get("spanId"),
            parent_span_id=otlp_span.get("parentSpanId"),
            name=otlp_span.get("name"),
            kind=otlp_span.get("kind", 0),
            start_time=int(otlp_span.get("startTimeUnixNano", 0)),
            end_time=int(otlp_span.get("endTimeUnixNano", 0)),
            duration_ns=int(otlp_span.get("endTimeUnixNano", 0)) - int(otlp_span.get("startTimeUnixNano", 0)),
            attributes=attributes,
            resource_attributes=resource_attrs,
            scope=otlp_span.get("_scope", {}).get("name", "unknown"),
            status=otlp_span.get("status", {})
        )
    
    def _group_spans_by_trace_id(self, spans: List[NormalizedSpan]) -> Dict[str, NormalizedTrace]:
        """Group spans into complete NormalizedTrace objects by traceId"""
        trace_spans = {}
        for span in spans:
            trace_id = span.trace_id
            if trace_id not in trace_spans:
                trace_spans[trace_id] = []
            trace_spans[trace_id].append(span)
        
        # Create NormalizedTrace objects with metadata
        traces = {}
        for trace_id, spans in trace_spans.items():
            if spans:
                metadata = TraceMetadata(
                    service_name=spans[0].resource_attributes.get("service.name", "unknown"),
                    total_duration_ns=max(s.end_time for s in spans) - min(s.start_time for s in spans),
                    span_count=len(spans),
                    start_time=min(s.start_time for s in spans),
                    end_time=max(s.end_time for s in spans)
                )
                traces[trace_id] = NormalizedTrace(
                    trace_id=trace_id,
                    spans=spans,
                    metadata=metadata
                )
        
        return traces

# Usage Example Functions

def load_traces_for_evaluation(traces_path: str = "eval/tracing/otel-traces.jsonl") -> Dict[str, NormalizedTrace]:
    """Standard function to load and normalize traces for evaluation"""
    extractor = TraceExtractor(traces_path)
    return extractor.load_and_normalize_traces()
```

#### Integration with Evaluation Pipeline

**Standard pattern: Normalize traces → Extract test cases → Run DeepEval metrics**:

**IMPORTANT**: Each metric requires specific data extractions. Implement helper functions based on your evaluation needs:

```python
# In your main evaluation script
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from trace_extractor import load_traces_for_evaluation

# Generic extraction helpers (customize based on your agent's trace structure)
def extract_input(trace: NormalizedTrace) -> str:
    """Extract user input from trace - customize for your agent"""
    workflow_spans = trace.find_spans(name_contains="workflow")
    if workflow_spans:
        main_workflow = workflow_spans[0]
        return main_workflow.attributes.get("traceloop.entity.input", "")
    return ""

def extract_output(trace: NormalizedTrace) -> str:
    """Extract final agent output from trace - customize for your agent"""
    agent_spans = trace.find_spans(name_contains="agent")
    if agent_spans:
        # Get the last agent span's output as final answer
        final_span = max(agent_spans, key=lambda s: s.end_time)
        return final_span.attributes.get("traceloop.entity.output", "")
    return ""

# Metric-specific extraction helpers
def extract_retrieval_context_for_faithfulness(trace: NormalizedTrace) -> list:
    """Extract RAG context specifically for FaithfulnessMetric"""
    retrieval_spans = trace.find_spans(name_contains="retrieval")
    context = []
    for span in retrieval_spans:
        docs = span.attributes.get("traceloop.entity.output", "")
        if docs:
            context.append(docs)
    return context

def extract_tool_calls_for_custom_metric(trace: NormalizedTrace) -> list:
    """Extract tool call data for custom tool evaluation metrics"""
    tool_spans = trace.find_spans(name_contains="tool")
    tool_calls = []
    for span in tool_spans:
        tool_calls.append({
            "tool_name": span.attributes.get("tool.name", ""),
            "input": span.attributes.get("traceloop.entity.input", ""),
            "output": span.attributes.get("traceloop.entity.output", "")
        })
    return tool_calls

# Load normalized traces
traces = load_traces_for_evaluation("eval/tracing/otel-traces.jsonl")

# Define evaluation metrics (each may need different LLMTestCase fields)
metrics = [
    FaithfulnessMetric(threshold=0.7),      # Needs: input, actual_output, retrieval_context
    AnswerRelevancyMetric(threshold=0.8),   # Needs: input, actual_output
    # CorrectnessMetric(threshold=0.9),     # Needs: input, actual_output, expected_output
    # CustomToolMetric(threshold=0.85),     # Needs: custom extraction for tool calls
]

# Convert traces to DeepEval test cases
test_cases = []
for trace_id, trace in traces.items():
    test_case = LLMTestCase(
        input=extract_input(trace),
        actual_output=extract_output(trace),
        retrieval_context=extract_retrieval_context_for_faithfulness(trace),
        # expected_output=extract_expected_output_for_correctness(trace),  # Add if needed
        # Add other fields as required by your specific metrics
    )
    test_cases.append(test_case)

# Run evaluation using DeepEval
results = evaluate(test_cases, metrics)
```

**Key Points**:
- **Metric-Specific Extraction**: Each metric type requires different data from traces
- **Customize Helper Functions**: Adapt extraction logic to your agent's specific trace structure
- **LLMTestCase Fields**: Only populate fields needed by your chosen metrics
- **Dynamic Extraction**: Use `NormalizedTrace` helper methods to find and extract relevant spans/attributes

#### Benefits of Unified Data Class Approach

1. **Flexibility**: AI can extract exactly what each metric needs without pre-defined constraints
2. **Consistency**: Standardized trace structure with type safety
3. **Performance**: Single normalization pass, then dynamic extraction as needed
4. **Maintainability**: Clean data model with helper methods for common operations
5. **Extensibility**: Easy to add new helper methods without changing core structure



## Common Pitfalls to Avoid

- **Over-Engineering**: Don't add complexity before the basic version works
- **Direct Agent Coupling**: Don't tightly couple evaluation to direct agent execution - prioritize trace-based evaluation
- **Missing Trace Normalization**: Don't proceed without validating trace data can be normalized to NormalizedTrace objects
- **Ignoring Trace-First Architecture**: Always implement normalization layer before evaluation logic
- **Agent Simulation**: Never mock or simulate the agent being evaluated
- **Hardcoded Values**: Use configuration files instead of embedding values in code
- **Silent Failures**: Always log errors and provide clear error messages
- **Incomplete Normalization**: Ensure all required trace data (spans, attributes, metadata) is properly normalized
- **Ignoring the Design**: Follow the established task structure and file organization


Report completion with implementation status and readiness for the next phase (`/evalkit.insights`).
