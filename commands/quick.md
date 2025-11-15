---
description: Run complete evaluation pipeline automatically
scripts:
  sh: scripts/bash/auto-pipeline.sh
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/evalkit.quick` in the triggering message **is** additional context for the entire evaluation pipeline. This meta-command runs the complete evaluation workflow automatically.

Given that context, do this:

1. Run the script `{SCRIPT} "$ARGUMENTS"` to execute the complete pipeline automatically.

2. Report completion with summary of all phases and final results location.