<div align="center">
    <h1>🔍 EvalKit</h1>
    <h3><em>Evaluate AI agents systematically.</em></h3>
</div>

<p align="center">
    <strong>A comprehensive framework for evaluating AI agents across multiple dimensions including quality, performance, robustness, and user experience.</strong>
</p>

---

## Table of Contents

- [🤔 What is Agent Evaluation?](#-what-is-agent-evaluation)
- [⚡ Get started](#-get-started)
- [🤖 Supported AI Assistants](#-supported-ai-assistants)
- [🔧 EvalKit CLI Reference](#-evalkit-cli-reference)
- [📚 Core philosophy](#-core-philosophy)
- [🌟 Evaluation dimensions](#-evaluation-dimensions)
- [🎯 Framework goals](#-framework-goals)
- [🔧 Prerequisites](#-prerequisites)
- [📖 Learn more](#-learn-more)
- [📋 Detailed process](#-detailed-process)
- [🔍 Troubleshooting](#-troubleshooting)
- [👥 Maintainers](#-maintainers)
- [💬 Support](#-support)
- [🙏 Acknowledgements](#-acknowledgements)
- [📄 License](#-license)

## 🤔 What is Agent Evaluation?

Agent Evaluation transforms ad-hoc testing into **systematic, reproducible evaluation workflows**. Instead of manually testing agents with random inputs, EvalKit provides a structured framework to comprehensively assess AI agents across multiple dimensions with measurable metrics and actionable insights.

## ⚡ Get started

### 1. Install EvalKit

Choose your preferred installation method:

#### Option 1: Persistent Installation (Recommended)

Install once and use everywhere:

```bash
uv tool install evalkit-cli --from git+https://github.com/github/eval-kit.git
```

Then use the tool directly:

```bash
evalkit init <PROJECT_NAME>
evalkit check
```

To upgrade evalkit run:

```bash
uv tool install evalkit-cli --force --from git+https://github.com/github/eval-kit.git
```

#### Option 2: One-time Usage

Run directly without installing:

```bash
uvx --from git+https://github.com/github/eval-kit.git evalkit init <PROJECT_NAME>
```

**Benefits of persistent installation:**

- Tool stays installed and available in PATH
- No need to create shell aliases
- Better tool management with `uv tool list`, `uv tool upgrade`, `uv tool uninstall`
- Cleaner shell configuration

### 2. Design evaluation strategy

Use the **`/evalkit.design`** command to analyze your agent and design a comprehensive evaluation strategy.

```bash
/evalkit.design Analyze my customer service chatbot agent and design evaluation strategy focusing on response accuracy, latency, and user satisfaction
```

### 3. Clarify evaluation requirements (optional)

Use the **`/evalkit.clarify`** command to clarify any underspecified areas in your evaluation design.

```bash
/evalkit.clarify
```

### 4. Create evaluation implementation plan

Use the **`/evalkit.plan`** command to create technical implementation plans for your evaluation infrastructure.

```bash
/evalkit.plan Use DeepEval for metrics computation, implement real-time monitoring, and create interactive dashboards for result visualization
```

### 5. Generate evaluation tasks

Use **`/evalkit.tasks`** to create an actionable task list from your evaluation plan.

```bash
/evalkit.tasks
```

### 6. Implement evaluation pipeline

Use **`/evalkit.implement`** to execute all tasks and build your evaluation pipeline according to the plan.

```bash
/evalkit.implement
```

### 7. Analyze results and get insights

Use **`/evalkit.insights`** to analyze evaluation results and get actionable improvement recommendations.

```bash
/evalkit.insights
```

For detailed step-by-step instructions, see our [comprehensive guide](./docs/quickstart.md).

## 🤖 Supported AI Assistants

| Assistant                                                     | Support | Notes                                             |
|---------------------------------------------------------------|---------|---------------------------------------------------|
| [Kilo Code](https://kilocode.ai)                              | ✅ |                                                   |
| [Claude Code](https://www.anthropic.com/claude-code)         | ✅ |                                                   |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | ✅ |                                                   |

## 🔧 EvalKit CLI Reference

The `evalkit` command supports the following options:

### Commands

| Command     | Description                                                    |
|-------------|----------------------------------------------------------------|
| `init`      | Initialize a new EvalKit project from the latest template      |
| `check`     | Check for installed tools (`git`, `claude`, `q`, `kilocode`)   |

### `evalkit init` Arguments & Options

| Argument/Option        | Type     | Description                                                                  |
|------------------------|----------|------------------------------------------------------------------------------|
| `<project-name>`       | Argument | Name for your new project directory (optional if using `--here`, or use `.` for current directory) |
| `--ai`                 | Option   | AI assistant to use: `kilocode`, `claude`, or `q`                           |
| `--script`             | Option   | Script variant to use: `sh` (bash/zsh) or `ps` (PowerShell)                 |
| `--ignore-agent-tools` | Flag     | Skip checks for AI agent tools like Claude Code                             |
| `--no-git`             | Flag     | Skip git repository initialization                                          |
| `--here`               | Flag     | Initialize project in the current directory instead of creating a new one   |
| `--force`              | Flag     | Force merge/overwrite when initializing in current directory (skip confirmation) |
| `--skip-tls`           | Flag     | Skip SSL/TLS verification (not recommended)                                 |
| `--debug`              | Flag     | Enable detailed debug output for troubleshooting                            |
| `--github-token`       | Option   | GitHub token for API requests (or set GH_TOKEN/GITHUB_TOKEN env variable)  |

### Examples

```bash
# Basic project initialization
evalkit init my-agent-evaluation

# Initialize with specific AI assistant
evalkit init my-evaluation --ai kilocode

# Initialize with Claude Code support
evalkit init my-evaluation --ai claude

# Initialize with Amazon Q CLI support
evalkit init my-evaluation --ai q

# Initialize with PowerShell scripts (Windows/cross-platform)
evalkit init my-evaluation --ai claude --script ps

# Initialize in current directory
evalkit init . --ai kilocode
# or use the --here flag
evalkit init --here --ai kilocode

# Force merge into current (non-empty) directory without confirmation
evalkit init . --force --ai claude
# or 
evalkit init --here --force --ai claude

# Skip git initialization
evalkit init my-evaluation --ai q --no-git

# Enable debug output for troubleshooting
evalkit init my-evaluation --ai kilocode --debug

# Use GitHub token for API requests (helpful for corporate environments)
evalkit init my-evaluation --ai claude --github-token ghp_your_token_here

# Check system requirements
evalkit check
```

### Available Slash Commands

After running `evalkit init`, your AI coding assistant will have access to these slash commands for structured agent evaluation:

#### Core Commands

Essential commands for the Agent Evaluation workflow:

| Command                  | Description                                                           |
|--------------------------|-----------------------------------------------------------------------|
| `/evalkit.design`        | Analyze agent and design evaluation strategy                          |
| `/evalkit.clarify`       | Clarify underspecified areas (recommended before `/evalkit.plan`)    |
| `/evalkit.plan`          | Create evaluation implementation plan                                  |
| `/evalkit.tasks`         | Generate evaluation task lists                                        |
| `/evalkit.implement`     | Execute evaluation pipeline implementation                             |
| `/evalkit.insights`      | Analyze results and provide improvement suggestions                    |

### Environment Variables

| Variable         | Description                                                                                    |
|------------------|------------------------------------------------------------------------------------------------|
| `EVALKIT_FEATURE` | Override feature detection for non-Git repositories. Set to the feature directory name (e.g., `001-chatbot-evaluation`) to work on a specific evaluation when not using Git branches.<br/>**Must be set in the context of the agent you're working with prior to using `/evalkit.plan` or follow-up commands. |

## 📚 Core philosophy

Agent Evaluation with EvalKit emphasizes:

- **Real Agent Focus** where evaluations test actual agents, never simulations
- **Comprehensive Assessment** across quality, performance, robustness, and user experience
- **Systematic Methodology** rather than ad-hoc testing approaches
- **Actionable Insights** with specific improvement recommendations backed by evidence

## 🌟 Evaluation dimensions

| Dimension | Focus | Key Metrics |
|-----------|-------|-------------|
| **Quality** | Accuracy & Correctness | <ul><li>Response accuracy</li><li>Task completion rate</li><li>Output quality scores</li><li>Faithfulness to instructions</li></ul> |
| **Performance** | Speed & Efficiency | <ul><li>Response latency</li><li>Throughput capacity</li><li>Resource utilization</li><li>Cost per interaction</li></ul> |
| **Robustness** | Edge cases & Reliability | <ul><li>Error handling</li><li>Edge case performance</li><li>Failure recovery</li><li>Consistency across scenarios</li></ul> |
| **User Experience** | Usability & Satisfaction | <ul><li>Response clarity</li><li>Interaction quality</li><li>User satisfaction scores</li><li>Helpfulness ratings</li></ul> |

## 🎯 Framework goals

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

## 🔧 Prerequisites

- **Linux/macOS** (or WSL2 on Windows)
- AI coding assistant: [Kilo Code](https://kilocode.ai), [Claude Code](https://www.anthropic.com/claude-code), or [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

If you encounter issues with an assistant, please open an issue so we can refine the integration.

## 📖 Learn more

- **[Complete Agent Evaluation Methodology](./docs/quickstart.md)** - Deep dive into the full process
- **[Detailed Walkthrough](#-detailed-process)** - Step-by-step implementation guide

---

## 📋 Detailed process

<details>
<summary>Click to expand the detailed step-by-step walkthrough</summary>

You can use the EvalKit CLI to bootstrap your evaluation project, which will bring in the required artifacts in your environment. Run:

```bash
evalkit init <project_name>
```

Or initialize in the current directory:

```bash
evalkit init .
# or use the --here flag
evalkit init --here
# Skip confirmation when the directory already has files
evalkit init . --force
# or
evalkit init --here --force
```

You will be prompted to select the AI assistant you are using. You can also proactively specify it directly in the terminal:

```bash
evalkit init <project_name> --ai kilocode
evalkit init <project_name> --ai claude
evalkit init <project_name> --ai q

# Or in current directory:
evalkit init . --ai kilocode
evalkit init . --ai claude

# or use --here flag
evalkit init --here --ai kilocode
evalkit init --here --ai q

# Force merge into a non-empty current directory
evalkit init . --force --ai claude

# or
evalkit init --here --force --ai kilocode
```

The CLI will check if you have the required AI assistant tools installed. If you do not, or you prefer to get the templates without checking for the right tools, use `--ignore-agent-tools` with your command:

```bash
evalkit init <project_name> --ai claude --ignore-agent-tools
```

### **STEP 1:** Design evaluation strategy

Go to the project folder and run your AI assistant. In our example, we're using Kilo Code.

You will know that things are configured correctly if you see the `/evalkit.design`, `/evalkit.clarify`, `/evalkit.plan`, `/evalkit.tasks`, `/evalkit.implement`, and `/evalkit.insights` commands available.

The first step should be analyzing your agent and designing an evaluation strategy using the `/evalkit.design` command:

```text
/evalkit.design Analyze my customer service chatbot agent located in ./src/chatbot.py and design a comprehensive evaluation strategy focusing on response accuracy, conversation flow, and user satisfaction metrics.
```

This step creates the evaluation specification that defines what aspects of your agent will be evaluated and how.

### **STEP 2:** Clarify evaluation requirements (optional)

With your evaluation design established, you can clarify any underspecified areas. Use the `/evalkit.clarify` command to identify and resolve ambiguities:

```text
/evalkit.clarify
```

This step helps ensure your evaluation strategy is comprehensive and addresses all important aspects of agent performance.

### **STEP 3:** Create evaluation implementation plan

You can now specify the technical details for implementing your evaluation. Use the `/evalkit.plan` command:

```text
/evalkit.plan Use DeepEval for LLM-based metrics, implement real-time monitoring with custom dashboards, store results in JSON format, and create automated reporting pipeline.
```

The output of this step will include implementation details for your evaluation infrastructure.

### **STEP 4:** Generate evaluation tasks

Use the `/evalkit.tasks` command to break down your evaluation plan into actionable tasks:

```text
/evalkit.tasks
```

This creates a structured task list that can be executed systematically.

### **STEP 5:** Implement evaluation pipeline

Once ready, use the `/evalkit.implement` command to execute your implementation plan:

```text
/evalkit.implement
```

The `/evalkit.implement` command will:
- Set up the evaluation environment and dependencies
- Import and configure your actual agent (no simulations)
- Implement data processing pipelines
- Create metrics computation engines
- Build monitoring and reporting systems

>[!IMPORTANT]
>The AI assistant will execute local CLI commands and import your actual agent code - make sure your agent is properly set up and all dependencies are installed.

### **STEP 6:** Analyze results and get insights

After running your evaluation, use the `/evalkit.insights` command to analyze results:

```text
/evalkit.insights
```

This will provide:
- Performance analysis and trend identification
- Specific improvement recommendations with evidence
- Comparative analysis against benchmarks
- Actionable optimization suggestions

</details>

---

## 🔍 Troubleshooting

### Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, you can install Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```

## 👥 Maintainers

- Kang Zhou ([@kangISU](https://github.com/kangISU))

## 💬 Support

For support, please open a [GitHub issue](https://github.com/github/eval-kit/issues/new). We welcome bug reports, feature requests, and questions about using Agent Evaluation with EvalKit.

## 🙏 Acknowledgements

This project evolved from Spec Kit, transforming from a software development specification toolkit into a comprehensive agent evaluation framework.

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.
