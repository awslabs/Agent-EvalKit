---
title: Overview
description: What Agent-EvalKit does and what to expect from it.
---

**Agent-EvalKit** automates the evaluation process for your AI agents. It runs as a set of commands inside your
AI coding assistant and writes an evaluation pipeline into your project, so you end up with ordinary code that you
own and can change.

## What it does

1. Create an evaluation plan by analyzing your agent and your requirements
2. Generate test cases for the evaluation
3. Add tracing instrumentation to your agent (optional)
4. Run your agent and collect execution traces
5. Write and run evaluation code to assess performance
6. Generate a report with recommendations for improving the agent

## What to expect

EvalKit generates an evaluation pipeline quickly, as a starting point you refine for your own requirements.

- **Review the code.** Check that it works as expected for your agent.
- **Customize it.** Adapt the pipeline to your specific requirements.

## Supported assistants

EvalKit currently supports [Kiro CLI](https://kiro.dev/cli/), [Claude Code](https://www.anthropic.com/claude-code),
and [Kilo Code](https://kilocode.ai).

## Acknowledgements

Agent-EvalKit evolved from an autonomous Evaluation Agent project. Inspired by
[spec-kit](https://github.com/github/spec-kit), it is packaged as a toolkit that works with multiple coding
assistants.
