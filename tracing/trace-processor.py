#!/usr/bin/env python3
# trace-processor.py
# Convert OTLP traces (JSONL from OpenTelemetry Collector "file" exporter) into
# minimal flat JSON for evaluation purposes with intelligent agent workflow filtering.
#
# Usage:
#   python trace-processor.py --input ./otel-traces.jsonl --output-dir ./processed_traces/ [--pretty]
#
# Features:
# - Intelligent filtering: Only includes spans with traceloop.*, gen_ai.*, or http.* attributes
# - Excludes entire traces that contain no agent workflow spans
# - Extracts essential evaluation fields: entity_name, entity_input, entity_output
# - Flexible gen_ai extraction supporting multiple attribute patterns:
#   * Standard: gen_ai.prompt.{i}.role + gen_ai.prompt.{i}.content
#   * Alternative: gen_ai.prompt.{i}.{role} (role embedded in attribute name)
# - Extracts gen_ai metadata: system, model, request_type
# - Extracts HTTP span details: method, url, status_code
# - Creates individual trace files for easy evaluation processing
#
# Output format (per trace file: <traceId>.json):
# {
#   "traceId": "...",
#   "spans": [
#      {
#        "spanId": "...",
#        "parentSpanId": "...",
#        "start_time": 1762390996052427000,
#        "duration_ms": 12.34,
#        "entity_name": "...",           # from traceloop.entity.name
#        "entity_input": "...",          # from traceloop.entity.input (raw JSON string)
#        "entity_output": "...",         # from traceloop.entity.output (raw JSON string)
#        "gen_ai_system": "...",         # from gen_ai.system (when present)
#        "gen_ai_model": "...",          # from gen_ai.request.model (when present)
#        "llm_request_type": "...",      # from llm.request.type (when present)
#        "gen_ai_prompts": [...],        # list of prompt messages (when present)
#        "gen_ai_completions": [...],    # list of completion messages (when present)
#        "http_method": "...",           # from http.method (when present)
#        "http_url": "...",              # from http.url (when present)
#        "http_status_code": 200         # from http.status_code (when present)
#      }
#   ]
# }
#
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple


def attr_list_to_dict(attrs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert OTLP attributes format (list of {'key', 'value': {...}}) to a simple dict."""
    out = {}
    for item in attrs or []:
        key = item.get("key")
        v = item.get("value", {})
        # OTLP JSON uses oneof-like: {"stringValue": "..."} or {"intValue": "..."} etc.
        if "stringValue" in v:
            val = v["stringValue"]
        elif "intValue" in v:
            val = int(v["intValue"])
        elif "doubleValue" in v:
            val = float(v["doubleValue"])
        elif "boolValue" in v:
            val = bool(v["boolValue"])
        elif "arrayValue" in v:
            # arrayValue: {"values": [ {"stringValue": ...}, ... ]}
            arr = []
            for av in v.get("arrayValue", {}).get("values", []):
                # recurse shallowly for scalar types
                if "stringValue" in av:
                    arr.append(av["stringValue"])
                elif "intValue" in av:
                    arr.append(int(av["intValue"]))
                elif "doubleValue" in av:
                    arr.append(float(av["doubleValue"]))
                elif "boolValue" in av:
                    arr.append(bool(av["boolValue"]))
                else:
                    arr.append(av)  # fallback raw
            val = arr
        elif "kvlistValue" in v:
            # kvlistValue: {"values": [ {"key": "...","value":{...}}, ... ]}
            val = {kv.get("key"): kv.get("value") for kv in v.get("kvlistValue", {}).get("values", [])}
        else:
            val = v  # as-is fallback
        if key is not None:
            out[key] = val
    return out


def extract_gen_ai_prompts(attrs: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract gen_ai prompt messages from attributes."""
    prompts = []
    i = 0
    while True:
        # Check for standard pattern: gen_ai.prompt.{i}.role and gen_ai.prompt.{i}.content
        role_key = f"gen_ai.prompt.{i}.role"
        content_key = f"gen_ai.prompt.{i}.content"

        if role_key in attrs and content_key in attrs:
            prompts.append({"role": attrs[role_key], "content": attrs[content_key]})
            i += 1
            continue

        # Check for alternative pattern: gen_ai.prompt.{i}.{role} (e.g., gen_ai.prompt.0.user)
        found_alternative = False
        for role in ["user", "assistant", "system"]:
            alt_key = f"gen_ai.prompt.{i}.{role}"
            if alt_key in attrs:
                prompts.append({"role": role, "content": attrs[alt_key]})
                found_alternative = True
                break

        if found_alternative:
            i += 1
            continue

        # No more prompts found
        break

    return prompts


def extract_gen_ai_completions(attrs: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract gen_ai completion messages from attributes."""
    completions = []
    i = 0
    while True:
        # Check for standard pattern: gen_ai.completion.{i}.role and gen_ai.completion.{i}.content
        role_key = f"gen_ai.completion.{i}.role"
        content_key = f"gen_ai.completion.{i}.content"

        if role_key in attrs and content_key in attrs:
            completions.append({"role": attrs[role_key], "content": attrs[content_key]})
            i += 1
            continue

        # Check for alternative pattern: gen_ai.completion.{i}.{role} (e.g., gen_ai.completion.0.assistant)
        found_alternative = False
        for role in ["user", "assistant", "system"]:
            alt_key = f"gen_ai.completion.{i}.{role}"
            if alt_key in attrs:
                completions.append({"role": role, "content": attrs[alt_key]})
                found_alternative = True
                break

        if found_alternative:
            i += 1
            continue

        # No more completions found
        break

    return completions


def extract_gen_ai_metadata(attrs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract gen_ai metadata attributes."""
    metadata = {}

    if "gen_ai.system" in attrs:
        metadata["gen_ai_system"] = attrs["gen_ai.system"]
    if "gen_ai.request.model" in attrs:
        metadata["gen_ai_model"] = attrs["gen_ai.request.model"]
    if "llm.request.type" in attrs:
        metadata["llm_request_type"] = attrs["llm.request.type"]

    return metadata


def extract_http_attributes(attrs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract HTTP-specific attributes for POST/GET spans."""
    http_attrs = {}

    if "http.method" in attrs:
        http_attrs["http_method"] = attrs["http.method"]
    if "http.url" in attrs:
        http_attrs["http_url"] = attrs["http.url"]
    if "http.status_code" in attrs:
        http_attrs["http_status_code"] = attrs["http.status_code"]

    return http_attrs


def extract_otel_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract OpenTelemetry events (user messages, assistant messages, tool calls)."""
    result = {}
    prompts = []
    completions = []

    for event in events or []:
        event_name = event.get("name", "")
        event_attrs = attr_list_to_dict(event.get("attributes", []))

        if event_name == "gen_ai.user.message":
            content = event_attrs.get("content")
            if content:
                prompts.append({"role": "user", "content": content})
        elif event_name == "gen_ai.assistant.message":
            content = event_attrs.get("content")
            if content:
                completions.append({"role": "assistant", "content": content})
        elif event_name == "gen_ai.choice":
            message = event_attrs.get("message")
            if message:
                completions.append({"role": "assistant", "content": message})
        elif event_name == "gen_ai.tool.message":
            content = event_attrs.get("content")
            role = event_attrs.get("role", "tool")
            if content:
                if role == "tool":
                    completions.append({"role": "tool", "content": content})
                else:
                    prompts.append({"role": role, "content": content})

    if prompts:
        result["gen_ai_prompts"] = prompts
    if completions:
        result["gen_ai_completions"] = completions

    return result


def extract_additional_gen_ai_attrs(attrs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract additional OpenTelemetry gen_ai attributes."""
    additional = {}

    # Tool information
    if "gen_ai.tool.name" in attrs:
        additional["gen_ai_tool_name"] = attrs["gen_ai.tool.name"]
    if "gen_ai.tool.description" in attrs:
        additional["gen_ai_tool_description"] = attrs["gen_ai.tool.description"]

    # Agent information
    if "gen_ai.agent.name" in attrs:
        additional["gen_ai_agent_name"] = attrs["gen_ai.agent.name"]

    return additional


def is_agent_workflow_span(attrs: Dict[str, Any]) -> bool:
    """Check if span is part of agent workflow."""
    # Check for traceloop attributes (indicates agent workflow)
    for key in attrs:
        if key.startswith("traceloop."):
            return True

    # Also check for gen_ai or http attributes (OpenTelemetry agent workflows)
    for key in attrs:
        if key.startswith("gen_ai.") or key.startswith("http."):
            return True

    return False


def collect_spans_from_request(req: Dict[str, Any]) -> List[Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]]:
    """Return list of tuples (resource_attrs, scope_info, span_dict)."""
    out = []
    for rs in req.get("resourceSpans", []) or []:
        resource_attrs = attr_list_to_dict(rs.get("resource", {}).get("attributes", []))
        for ss in rs.get("scopeSpans", []) or []:
            scope = ss.get("scope", {}) or {}
            scope_info = {"name": scope.get("name"), "version": scope.get("version")}
            for sp in ss.get("spans", []) or []:
                out.append((resource_attrs, scope_info, sp))
    return out


def normalize_span_minimal(
    resource_attrs: Dict[str, Any], scope_info: Dict[str, Any], sp: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract only essential fields for evaluation."""
    attrs = attr_list_to_dict(sp.get("attributes", []))

    # Get timing information
    start = sp.get("startTimeUnixNano")
    end = sp.get("endTimeUnixNano")
    dur_ms = None
    try:
        if start is not None and end is not None:
            dur_ms = (int(end) - int(start)) / 1e6
    except Exception:
        pass

    # Extract traceloop fields (for traceloop traces)
    entity_name = attrs.get("traceloop.entity.name")
    entity_input_raw = attrs.get("traceloop.entity.input")
    entity_output_raw = attrs.get("traceloop.entity.output")

    # Extract OpenTelemetry gen_ai operation name (fallback for entity_name)
    if entity_name is None:
        entity_name = attrs.get("gen_ai.operation.name")

    # Build minimal structure with only essential fields
    node = {
        "spanId": sp.get("spanId"),
        "parentSpanId": sp.get("parentSpanId", ""),
        "start_time": int(start) if start is not None else None,
        "duration_ms": dur_ms,
    }

    # Add entity name (from traceloop or gen_ai)
    if entity_name is not None:
        node["entity_name"] = entity_name

    # Add traceloop fields if they exist (keep as raw strings)
    if entity_input_raw is not None:
        node["entity_input"] = entity_input_raw
    if entity_output_raw is not None:
        node["entity_output"] = entity_output_raw

    # Extract gen_ai metadata if present (before prompts/completions)
    gen_ai_metadata = extract_gen_ai_metadata(attrs)
    if gen_ai_metadata:
        node.update(gen_ai_metadata)

    # Extract gen_ai prompts and completions from attributes (traceloop style)
    gen_ai_prompts = extract_gen_ai_prompts(attrs)
    gen_ai_completions = extract_gen_ai_completions(attrs)

    if gen_ai_prompts:
        node["gen_ai_prompts"] = gen_ai_prompts
    if gen_ai_completions:
        node["gen_ai_completions"] = gen_ai_completions

    # Extract OpenTelemetry events (user/assistant messages, tool calls)
    otel_events = extract_otel_events(sp.get("events", []))
    if otel_events:
        # Merge with existing prompts/completions, prioritizing events
        if "gen_ai_prompts" in otel_events:
            node["gen_ai_prompts"] = otel_events["gen_ai_prompts"]
        if "gen_ai_completions" in otel_events:
            node["gen_ai_completions"] = otel_events["gen_ai_completions"]

    # Extract additional gen_ai attributes (tool info, usage, etc.)
    additional_attrs = extract_additional_gen_ai_attrs(attrs)
    if additional_attrs:
        node.update(additional_attrs)

    # Extract HTTP attributes if present (for POST/GET spans)
    http_attrs = extract_http_attributes(attrs)
    if http_attrs:
        node.update(http_attrs)

    return node


def build_flat_traces(nodes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Group by traceId and create flat lists ordered by start time. Skip traces with no spans."""
    traces: Dict[str, Dict[str, Any]] = {}

    # Group spans by trace ID
    per_trace_spans: Dict[str, List[Dict[str, Any]]] = {}
    for n in nodes:
        tid = n.get("traceId") or "unknown-trace"
        if tid not in per_trace_spans:
            per_trace_spans[tid] = []
        # Remove traceId from individual spans since it's at trace level
        span_data = {k: v for k, v in n.items() if k != "traceId"}
        per_trace_spans[tid].append(span_data)

    # Sort spans by start time within each trace and skip empty traces
    for tid, spans in per_trace_spans.items():
        # Skip traces with no spans (all spans were filtered out)
        if not spans:
            continue

        # Sort by start_time, with None values at the end
        spans.sort(key=lambda x: x.get("start_time") or float("inf"))

        traces[tid] = {
            "traceId": tid,
            "spans": spans,
        }

    return traces


def main():
    ap = argparse.ArgumentParser(description="Convert OTLP traces to minimal evaluation format")
    ap.add_argument("--input", "-i", required=True, help="Path to otel-traces.jsonl from collector file exporter")
    ap.add_argument("--output-dir", "-o", required=True, help="Directory to write individual trace JSON files")
    ap.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[ERROR] Input not found: {in_path}", file=sys.stderr)
        sys.exit(2)

    # Create output directory
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_nodes: List[Dict[str, Any]] = []

    with in_path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[WARN] line {ln}: JSON decode error: {e}", file=sys.stderr)
                continue

            # Only process resourceSpans
            if "resourceSpans" not in req:
                continue

            for resource_attrs, scope_info, sp in collect_spans_from_request(req):
                # Check if span is part of agent workflow
                attrs = attr_list_to_dict(sp.get("attributes", []))
                if not is_agent_workflow_span(attrs):
                    continue  # Skip spans that are not part of agent workflow

                # Store traceId in the span for later use
                sp_with_trace = {**sp, "traceId": sp.get("traceId")}
                node = normalize_span_minimal(resource_attrs, scope_info, sp_with_trace)
                # Keep traceId for grouping
                node["traceId"] = sp.get("traceId")
                all_nodes.append(node)

    traces = build_flat_traces(all_nodes)

    # Write each trace to a separate file
    for trace_id, trace_data in traces.items():
        trace_file = out_dir / f"{trace_id}.json"
        with trace_file.open("w", encoding="utf-8") as out_f:
            if args.pretty:
                json.dump(trace_data, out_f, ensure_ascii=False, indent=2)
            else:
                json.dump(trace_data, out_f, ensure_ascii=False)

    print(f"Wrote {len(traces)} individual trace files to {out_dir}")

    # Print summary of what was kept
    total_spans = sum(len(trace["spans"]) for trace in traces.values())
    print(f"Processed {total_spans} agent workflow spans in flat structure.")
    print("Filtered out spans without traceloop.*, gen_ai.*, or http.* attributes (non-agent workflow spans).")
    print("Kept only essential evaluation fields:")
    print("  - spanId, parentSpanId, start_time, duration_ms")
    print("  - entity_name (logical operation name from traceloop.entity.name or gen_ai.operation.name)")
    print("  - entity_input (raw JSON string from traceloop.entity.input)")
    print("  - entity_output (raw JSON string from traceloop.entity.output)")
    print("  - gen_ai_prompts (when present, from attributes or events)")
    print("  - gen_ai_completions (when present, from attributes or events)")
    print("  - gen_ai_system, gen_ai_model, llm_request_type (when present)")
    print("  - gen_ai_tool_name, gen_ai_agent_name (when present)")
    print("  - http_method, http_url, http_status_code (for HTTP spans)")
    print(f"Each trace saved as: <traceId>.json in {out_dir}")


if __name__ == "__main__":
    main()
