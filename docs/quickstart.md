# Quick Start Guide

This guide will help you get started with Agent Evaluation using EvalKit.

> NEW: All automation scripts now provide both Bash (`.sh`) and PowerShell (`.ps1`) variants. The `evalkit` CLI auto-selects based on OS unless you pass `--script sh|ps`.

## The 6-Step Evaluation Process

### 1. Install EvalKit

Initialize your evaluation project depending on the AI assistant you're using:

```bash
uvx --from git+https://github.com/github/eval-kit.git evalkit init <PROJECT_NAME>
```

Pick script type explicitly (optional):
```bash
uvx --from git+https://github.com/github/eval-kit.git evalkit init <PROJECT_NAME> --script ps  # Force PowerShell
uvx --from git+https://github.com/github/eval-kit.git evalkit init <PROJECT_NAME> --script sh  # Force POSIX shell
```

### 2. Design Evaluation Strategy

Use the `/evalkit.design` command to analyze your agent and design a comprehensive evaluation strategy.

```bash
/evalkit.design Analyze my customer service chatbot agent located in ./src/chatbot.py and design evaluation strategy focusing on response accuracy, conversation flow, and user satisfaction metrics.
```

### 3. Clarify Evaluation Requirements (Optional)

Use the `/evalkit.clarify` command to clarify any underspecified areas in your evaluation design.

```bash
/evalkit.clarify
```

### 4. Create Evaluation Implementation Plan

Use the `/evalkit.plan` command to create technical implementation plans for your evaluation infrastructure.

```bash
/evalkit.plan Use DeepEval for LLM-based metrics, implement real-time monitoring with custom dashboards, store results in JSON format, and create automated reporting pipeline.
```

### 5. Generate and Execute Tasks

Use `/evalkit.tasks` to create an actionable task list, then `/evalkit.implement` to build the evaluation pipeline.

```bash
/evalkit.tasks
/evalkit.implement
```

### 6. Analyze Results and Get Insights

Use `/evalkit.insights` to analyze evaluation results and get actionable improvement recommendations.

```bash
/evalkit.insights
```

## Detailed Example: Evaluating a Customer Service Chatbot

Here's a complete example of evaluating a customer service chatbot:

### Step 1: Design Evaluation Strategy with `/evalkit.design`

```text
Analyze my customer service chatbot agent that handles customer inquiries, processes refund requests, 
and provides product information. The agent uses RAG with a knowledge base and has access to order 
lookup tools. I want to evaluate response accuracy, conversation flow quality, tool usage effectiveness, 
and customer satisfaction. Focus on real-world scenarios including edge cases like unclear requests 
and system errors.
```

### Step 2: Clarify Requirements (Optional)

After the initial evaluation design is created, clarify any missing requirements:

```text
Should we include multi-turn conversation evaluation? What about testing with different customer personas 
(angry, confused, technical)? Do we need to test the agent's ability to escalate to human support?
```

### Step 3: Create Implementation Plan with `/evalkit.plan`

Be specific about your evaluation infrastructure and technical requirements:

```text
Use DeepEval for response quality metrics (relevance, faithfulness, coherence). Implement custom metrics 
for tool usage accuracy and conversation flow. Create test scenarios with synthetic customer data. 
Set up monitoring dashboard with real-time results. Store evaluation data in structured JSON format 
for analysis and reporting.
```

### Step 4: Generate Tasks and Implement

Generate the evaluation task breakdown:

```text
/evalkit.tasks
```

Then implement the evaluation pipeline:

```text
/evalkit.implement
```

### Step 5: Analyze Results

After running evaluations, analyze the results:

```text
/evalkit.insights
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

## Next Steps

- Read the complete evaluation methodology for in-depth guidance
- Check out the legacy evaluation agents in `legacy-eval-agent/` directory
- Explore evaluation examples and templates
- Review the source code on GitHub
