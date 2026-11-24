---
title: Installation
description: Requirements and installation for Agent-EvalKit.
---

## Requirements

- **System:** Linux or macOS, [Python 3.11+](https://www.python.org/downloads/), [uv](https://docs.astral.sh/uv/),
  and [Git](https://git-scm.com/downloads)
- **AI assistant:** [Kiro CLI](https://kiro.dev/cli/), [Claude Code](https://www.anthropic.com/claude-code), or
  [Kilo Code](https://kilocode.ai)

## Install EvalKit

Install once and use it everywhere:

```bash
uv tool install evalkit --from git+https://github.com/awslabs/Agent-EvalKit.git
```

To upgrade later:

```bash
uv tool install evalkit --force --from git+https://github.com/awslabs/Agent-EvalKit.git
```

Check that the prerequisites are in place:

```bash
evalkit check
```
