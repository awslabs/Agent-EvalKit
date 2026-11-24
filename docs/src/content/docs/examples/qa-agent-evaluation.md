---
title: QA agent evaluation
description: A complete EvalKit workflow on a question-answering agent.
---

The [`examples/qa_agent_evaluation/`](https://github.com/awslabs/Agent-EvalKit/tree/main/examples/qa_agent_evaluation)
folder shows a complete evaluation workflow produced with EvalKit:

- `qa_agent/` holds the agent under evaluation.
- `eval/` holds the evaluation pipeline EvalKit generated: the plan, the test cases, the traces, the evaluation code,
  and the report.

To reproduce it, follow the [quick start](../../guides/quick-start/) with the QA agent as the agent to evaluate.
