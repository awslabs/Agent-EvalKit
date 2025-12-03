<div align="center">
    <h1>Agent-EvalKit</h1>
</div>

<div align="center">
    <img src="media/agent-evalkit.gif" alt="Agent-EvalKit demo" width="720" />
</div>

<p align="center">
    <strong>AI assistant that automates evaluation processes for your AI agents.</strong>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [What to Expect](#what-to-expect-from-evalkit)
- [Reference](#reference)
- [Acknowledgements](#acknowledgements)

## Overview

**Agent-EvalKit** automates the complex evaluation process for your AI agents.

**Key Features:**

```
1. Create evaluation plan by analyzing agent and user requirements
2. Generate test cases for evaluation
3. Add tracing instrumentation to your agent (Optional)
4. Run your agent and collect execution traces
5. Write and run evaluation code to assess performance
6. Generate report with agent improvement recommendations
```

## Requirements

**System:** Linux/macOS • [Python 3.11+](https://www.python.org/downloads/) • [uv](https://docs.astral.sh/uv/) • [Git](https://git-scm.com/downloads)

**AI Assistant:** Currently supports [Kiro CLI](https://kiro.dev/cli/), [Claude Code](https://www.anthropic.com/claude-code), and [Kilo Code](https://kilocode.ai).

## Quick Start

### 1. Install EvalKit

```bash
# Install once and use everywhere
uv tool install evalkit --from git+https://github.com/awslabs/Agent-EvalKit.git

# To upgrade later
uv tool install evalkit --force --from git+https://github.com/awslabs/Agent-EvalKit.git
```

### 2. Initialize Evaluation Project

> **Important**:
> Ensure your agent to be evaluated runs successfully with all dependencies and API keys available locally before proceeding with evaluation using EvalKit.

```bash
# Create dedicated evaluation project
evalkit init my-agent-evaluation
cd my-agent-evaluation

# Copy your agent folder into the evaluation project
cp -r /path/to/your/agent-folder .
# This ensures reliable path resolution and artifact management throughout the evaluation process

# Start your AI assistant (example shown for Claude Code)
claude
# When prompted, agree to use Context7 MCP for documentation access
# Type /evalkit to see available commands

# Note: For Kilo Code and Kiro CLI, detailed setup instructions will be shown
# in the terminal after running 'evalkit init my-agent-evaluation'
```

### 3. Evaluate Your Agent

> **See Complete Example**: Check out [`examples/qa_agent_evaluation/`](examples/qa_agent_evaluation/) for a full evaluation workflow demonstration.

**Option A: Guided workflow (recommended for first-time users)**

```bash
/evalkit.quick
# This command will guide you through the whole evaluation process.
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

EvalKit automatically generates an evaluation pipeline that you can further refine according to your specific requirements.

### What You Do Next

- **Review the code**: Check if it works as expected for your agent
- **Customize based on your needs**: Adapt the evaluation pipeline for your specific requirements

## Reference

### CLI Commands

| Command                       | Description                       |
| ----------------------------- | --------------------------------- |
| `evalkit init <project-name>` | Initialize new evaluation project |
| `evalkit check`               | Check system prerequisites        |

### EvalKit Commands (Available after `evalkit init`)

| Command              | Description                                             |
| -------------------- | ------------------------------------------------------- |
| `/evalkit.quick`     | Step-by-step evaluation guide                           |
| `/evalkit.plan`      | Analyze agent and design evaluation strategy            |
| `/evalkit.data`      | Generate test cases for evaluation                      |
| `/evalkit.trace`     | Add tracing to your agent                               |
| `/evalkit.run_agent` | Run agent and collect traces                            |
| `/evalkit.eval`      | Write and execute evaluation code over traces           |
| `/evalkit.report`    | Analyze results and provide improvement recommendations |

---

## Acknowledgements

Agent-EvalKit evolved from our autonomous Evaluation Agent project. Inspired by [spec-kit](https://github.com/github/spec-kit), we packaged it as a toolkit compatible with multiple coding assistants.
