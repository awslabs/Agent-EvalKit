# EvalKit

*Evaluate AI agents systematically.*

**A comprehensive framework for evaluating AI agents across multiple dimensions including quality, performance, robustness, and user experience.**

## What is Agent Evaluation?

Agent Evaluation transforms ad-hoc testing into **systematic, reproducible evaluation workflows**. Instead of manually testing agents with random inputs, EvalKit provides a structured framework to comprehensively assess AI agents across multiple dimensions with measurable metrics and actionable insights.

## Getting Started

- [Installation Guide](installation.md)
- [Quick Start Guide](quickstart.md)
- [Local Development](local-development.md)

## Core Philosophy

Agent Evaluation with EvalKit emphasizes:

- **Real Agent Focus** where evaluations test actual agents, never simulations
- **Comprehensive Assessment** across quality, performance, robustness, and user experience
- **Systematic Methodology** rather than ad-hoc testing approaches
- **Actionable Insights** with specific improvement recommendations backed by evidence

## Evaluation Dimensions

| Dimension | Focus | Key Metrics |
|-----------|-------|-------------|
| **Quality** | Accuracy & Correctness | <ul><li>Response accuracy</li><li>Task completion rate</li><li>Output quality scores</li><li>Faithfulness to instructions</li></ul> |
| **Performance** | Speed & Efficiency | <ul><li>Response latency</li><li>Throughput capacity</li><li>Resource utilization</li><li>Cost per interaction</li></ul> |
| **Robustness** | Edge cases & Reliability | <ul><li>Error handling</li><li>Edge case performance</li><li>Failure recovery</li><li>Consistency across scenarios</li></ul> |
| **User Experience** | Usability & Satisfaction | <ul><li>Response clarity</li><li>Interaction quality</li><li>User satisfaction scores</li><li>Helpfulness ratings</li></ul> |

## Framework Goals

Our evaluation framework focuses on:

### Real Agent Testing
- Evaluate actual agent implementations, never simulations or mocks
- Collect metrics from real execution data
- Validate agent behavior under realistic conditions

### Framework Integration
- Built-in support for DeepEval, RAGAS, and custom evaluation frameworks
- Seamless integration with existing agent codebases
- Flexible metric computation and scoring systems

### Actionable Insights
- Generate specific improvement recommendations with evidence
- Identify performance bottlenecks and optimization opportunities
- Provide comparative analysis and benchmarking capabilities

### Systematic Evaluation
- Structured workflow from design to insights
- Reproducible evaluation processes
- Comprehensive documentation and reporting

## Contributing

Please see our [Contributing Guide](https://github.com/github/eval-kit/blob/main/CONTRIBUTING.md) for information on how to contribute to this project.

## Support

For support, please check our [Support Guide](https://github.com/github/eval-kit/blob/main/SUPPORT.md) or open an issue on GitHub.
