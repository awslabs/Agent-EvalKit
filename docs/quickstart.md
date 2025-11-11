# Quick Start Guide

This guide will help you get started with trace-based Agent Evaluation using EvalKit.

> NEW: All automation scripts now provide both Bash (`.sh`) and PowerShell (`.ps1`) variants. The `evalkit` CLI auto-selects based on OS unless you pass `--script sh|ps`.

## The 5-Command Evaluation Process

### 1. Install EvalKit

Initialize your evaluation project depending on the AI assistant you're using:

```bash
uvx --from git+https://github.com/kangISU/eval-kit.git evalkit init <PROJECT_NAME>
```

Pick script type explicitly (optional):
```bash
uvx --from git+https://github.com/kangISU/eval-kit.git evalkit init <PROJECT_NAME> --script ps  # Force PowerShell
uvx --from git+https://github.com/kangISU/eval-kit.git evalkit init <PROJECT_NAME> --script sh  # Force POSIX shell
```

### 2. Design Evaluation Strategy

Use the `/evalkit.plan` command to analyze your agent and design a comprehensive trace-based evaluation strategy. **User input is required** for this command to specify your evaluation goals.

```bash
/evalkit.plan Analyze my customer service chatbot agent located in ./src/chatbot.py and design evaluation strategy focusing on response accuracy, conversation flow, and user satisfaction metrics using trace-based evaluation.
```

### 3. Generate Test Cases (if needed)

Use the `/evalkit.data` command to generate comprehensive test cases for your evaluation scenarios. **User input is optional** - the command will use design specifications if no input provided.

```bash
/evalkit.data Generate test cases covering customer service scenarios including edge cases, tool usage patterns, and conversation flows.
```

Or simply:
```bash
/evalkit.data
```

### 4. Set Up Tracing Instrumentation (if needed)

Use the `/evalkit.trace` command to add tracing instrumentation to your agent for trace-based evaluation. **User input is optional** - the command will use design specifications if no input provided.

```bash
/evalkit.trace Add Traceloop instrumentation to capture agent execution traces including LLM calls, tool usage, and workflow steps.
```

Or simply:
```bash
/evalkit.trace
```

### 5. Implement Evaluation Pipeline

Use `/evalkit.code` to build your trace-based evaluation pipeline with normalized trace processing. **User input is optional** - the command will follow the established design and prerequisites.

```bash
/evalkit.code
```

### 6. Analyze Results and Get Actionable Recommendations

Use `/evalkit.report` to analyze evaluation results and get actionable improvement recommendations. **User input is optional** - the command will analyze available results.

```bash
/evalkit.report
```

## Detailed Example: Evaluating a Customer Service Chatbot

Here's a complete example of evaluating a customer service chatbot:

### Step 1: Design Evaluation Strategy with `/evalkit.plan`

```text
Analyze my customer service chatbot agent that handles customer inquiries, processes refund requests,
and provides product information. The agent uses RAG with a knowledge base and has access to order
lookup tools. I want to evaluate response accuracy, conversation flow quality, tool usage effectiveness,
and customer satisfaction using trace-based evaluation. Focus on real-world scenarios including edge cases
like unclear requests and system errors.
```

### Step 2: Generate Test Cases with `/evalkit.data` (if needed)

Create comprehensive test scenarios:

```text
/evalkit.data Generate test cases covering customer service scenarios: product inquiries, refund requests,
order lookups, edge cases with unclear requests, and system error handling scenarios.
```

### Step 3: Set Up Tracing with `/evalkit.trace` (if needed)

Add tracing instrumentation to capture agent execution data:

```text
/evalkit.trace Add Traceloop instrumentation to capture LLM calls, RAG retrieval steps, tool usage,
and conversation flow for comprehensive trace-based evaluation.
```

### Step 4: Implement Evaluation Pipeline with `/evalkit.code`

Build the trace-based evaluation pipeline:

```text
/evalkit.code Use DeepEval for response quality metrics (relevance, faithfulness, coherence) with
trace-extracted data. Implement custom metrics for tool usage accuracy and conversation flow analysis.
Process normalized traces for comprehensive evaluation.
```

### Step 5: Analyze Results with `/evalkit.report`

After running evaluations, analyze the results:

```text
/evalkit.report Analyze trace-based evaluation results and provide actionable improvement recommendations
for response accuracy, tool usage optimization, and conversation flow enhancement.
```

## Key Principles

- **Real Agent Focus** - Always evaluate actual agents, never simulations
- **Comprehensive Coverage** - Test across quality, performance, robustness, and user experience
- **Evidence-Based Insights** - Provide specific recommendations backed by measured data
- **Systematic Approach** - Follow structured methodology for reproducible results
- **Actionable Outcomes** - Generate concrete improvement suggestions with implementation guidance

## Supported AI Assistants

EvalKit works with these AI coding assistants:

- **Kilo Code** - Full support for all evaluation commands
- **Claude Code** - Complete integration with evaluation workflow  
- **Amazon Q Developer CLI** - Full evaluation pipeline support
