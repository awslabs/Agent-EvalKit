---
title: Quick start
description: Initialize an evaluation project and evaluate your agent.
---

:::caution
Make sure the agent you want to evaluate runs successfully, with all dependencies and API keys available locally,
before you start.
:::

## Initialize an evaluation project

```bash
# Create a dedicated evaluation project
evalkit init my-agent-evaluation
cd my-agent-evaluation

# Copy your agent folder into the evaluation project
cp -r /path/to/your/agent-folder .

# Start your AI assistant (Claude Code shown here)
claude
# When prompted, agree to use the Context7 MCP server for documentation access
# Type /evalkit to see the available commands
```

For Kilo Code and Kiro CLI, setup instructions are printed in the terminal after you run `evalkit init`.

## Evaluate your agent

### Option A: guided workflow

Recommended for first-time users. One command walks you through every step:

```bash
/evalkit.quick Evaluate my search agent at ./search_agent for final response quality
```

### Option B: individual commands

| Step | Command | What it does |
| --- | --- | --- |
| 1 | `/evalkit.plan` | Analyze the agent and design the evaluation strategy |
| 2 | `/evalkit.data` | Generate test cases |
| 3 | `/evalkit.trace` | Add tracing to your agent (optional) |
| 4 | `/evalkit.run_agent` | Run the agent and collect traces |
| 5 | `/evalkit.eval` | Write and run evaluation code over the traces |
| 6 | `/evalkit.report` | Analyze results and recommend improvements |

For example:

```bash
/evalkit.plan Evaluate my search agent at ./search_agent for final response quality
/evalkit.data Focus on edge cases
```

See the [QA agent example](../../examples/qa-agent-evaluation/) for a complete workflow.
