<div align="center">
    <h1>Agent-EvalKit</h1>
</div>

<p align="center">
    <strong>A build-time assistant for creating agent evaluation systems.</strong>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [What to Expect](#what-to-expect-from-evalkit)
- [Reference](#reference)
- [For Developers](#for-developers)
- [Acknowledgements](#acknowledgements)

## Overview

**EvalKit enables post-execution evaluation** by capturing agent execution traces, then evaluating over traces.

**Workflow:**
```
1. Plan evaluation strategy by analyzing agent and user requirements
2. Generate test cases for evaluation
3. Add tracing instrumentation to agent (if needed)
4. Run the instrumented agent on test cases
5. Capture execution traces from agent runs
6. Evaluate agent performance using the captured traces
```

**Key Benefits:**
- **Post-execution evaluation** - Decouple evaluation logic from agent execution
- **Production-ready monitoring** - Evaluation code built during development works directly in production

## Requirements

**System:** Linux/macOS • [Python 3.11+](https://www.python.org/downloads/) • [uv](https://docs.astral.sh/uv/) • [Git](https://git-scm.com/downloads)

**AI Assistant:** Currently supports [Claude Code](https://www.anthropic.com/claude-code). Support for [Kilo Code](https://kilocode.ai) and [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) coming soon.

## Quick Start

### 1. Install EvalKit

```bash
# Install once and use everywhere
uv tool install evalkit --from git+https://github.com/awslabs/Agent-EvalKit.git

# To upgrade later
uv tool install evalkit --force --from git+https://github.com/awslabs/Agent-EvalKit.git
```

### 2. Initialize Evaluation Project

```bash
# Create dedicated evaluation project
evalkit init my-agent-evaluation
cd my-agent-evaluation

# Copy your agent folder into the evaluation project
cp -r /path/to/your/agent-folder .
# This ensures reliable path resolution and artifact management throughout the evaluation process

# Start Claude Code and connect to Context7 MCP
claude
# When prompted, agree to use Context7 MCP for documentation access
# Type / to see available commands
```

**Important**: Ensure your agent runs successfully with all dependencies and API keys available locally.

### 3. Evaluate Your Agent

**Option A: Guided workflow (recommended for first-time users)**
```bash
/evalkit.quick
```

**Option B: Individual commands (for experienced users)**

**Step 1:** Analyze agent and design evaluation strategy
```bash
/evalkit.plan  # user input required
# Example: /evalkit.plan Evaluate my search agent at ./search_agent for final response quality
```

**Step 2:** Generate test cases for evaluation
```bash
/evalkit.data  # user input optional
# Example: /evalkit.data Focus on edge cases
```

**Step 3:** Add tracing to your agent
```bash
/evalkit.trace  # user input optional
```

**Step 4:** Run agent and collect traces
```bash
/evalkit.run_agent  # user input optional
```

**Step 5:** Write and execute evaluation code over traces
```bash
/evalkit.eval  # user input optional
```

**Step 6:** Analyze results and provide improvement recommendations
```bash
/evalkit.report  # user input optional
```

## What to Expect from EvalKit

**EvalKit provides a basic working evaluation pipeline that you can further develope for your specific needs.**

### What You Do Next
- **Review the code**: Check if it works as expected for your agent
- **Customize based on your needs**: Adapt the evaluation pipeline for your specific requirements

## Reference

### CLI Commands

| Command | Description |
|---------|-------------|
| `evalkit init <project-name>` | Initialize new evaluation project |
| `evalkit check` | Check system prerequisites |

### EvalKit Commands (Available after `evalkit init`)

| Command | Description |
|---------|-------------|
| `/evalkit.quick` | Step-by-step evaluation guide |
| `/evalkit.plan` | Analyze agent and design evaluation strategy |
| `/evalkit.data` | Generate test cases for evaluation |
| `/evalkit.trace` | Add tracing to your agent |
| `/evalkit.run_agent` | Run agent and collect traces |
| `/evalkit.eval` | Write and execute evaluation code over traces |
| `/evalkit.report` | Analyze results and provide improvement recommendations |


## For Developers

If you want to contribute to EvalKit, see the [Local Development Guide](./docs/local-development.md).

---

## Acknowledgements

This project architecture was inspired by [spec-kit](https://github.com/github/spec-kit).