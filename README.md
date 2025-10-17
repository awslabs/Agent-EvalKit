<div align="center">
    <img src="./media/logo.png" alt="EvalKit Logo" width="200">
    <h1>EvalKit</h1>
    <h3><em>Evaluate AI agents systematically.</em></h3>
</div>

<p align="center">
    <strong>A comprehensive framework for evaluating AI agents across multiple dimensions including quality, performance, robustness, and user experience.</strong>
</p>

---

## ✨ Key Design Features

EvalKit stands out with thoughtfully designed architectural features that ensure reliable, consistent, and cutting-edge agent evaluation:

### 🔌 Built-in MCP Server Support

**Universal MCP Integration Across All AI Assistants**
- **Context7 MCP Server**: Automatically deployed with every project for accessing the latest library documentation and usage patterns
- **Always Current**: Ensures you're implementing with the latest library functionalities and best practices
- **Zero Configuration**: MCP servers are automatically configured and ready to use

**Why This Matters**: Instead of relying on potentially outdated training data, you get real-time access to current library documentation, API changes, and implementation patterns. This dramatically reduces implementation errors and ensures your evaluations use modern approaches.

### 🛠️ Built-in Bash Scripts for Deterministic Operations

**Reliable, Consistent Automation**
- **Prerequisite Checking**: Automated validation of project requirements and dependencies
- **Branch Management**: Consistent Git workflow management across all evaluation projects
- **Environment Setup**: Standardized project initialization and configuration

**Why This Matters**: Rather than asking AI assistants to perform these operations ad-hoc (which can be inconsistent), EvalKit provides battle-tested scripts that ensure reliable, repeatable results every time. This eliminates variability in project setup and management.

### 🎯 The Perfect Balance

EvalKit combines the **creativity and intelligence of AI assistants** for evaluation design and implementation with **deterministic, reliable automation** for infrastructure operations. This hybrid approach delivers:

- **Consistent Infrastructure**: Reliable project setup and management
- **Current Best Practices**: Always up-to-date library usage through MCP integration
- **Reduced Errors**: Automated validation and standardized workflows
- **Enhanced Productivity**: Focus on evaluation logic, not infrastructure concerns

---

## Table of Contents

- [✨ Key Design Features](#-key-design-features)
- [👨‍💻 For Developers](#-for-developers)
- [⚡ Get started (Users)](#-get-started-users)
- [🤖 Supported AI Assistants](#-supported-ai-assistants)
- [🔧 EvalKit CLI Reference](#-evalkit-cli-reference)
- [🔧 Prerequisites](#-prerequisites)
- [👥 Maintainers](#-maintainers)
- [🙏 Acknowledgements](#-acknowledgements)

## 👨‍💻 For Developers

If you want to contribute to EvalKit or modify templates/scripts, see the [Local Development Guide](./docs/local-development.md) for:

- Authentication setup for private repository access
- CLI development workflow and testing
- Template/script modification workflow
- Release process and best practices

## ⚡ Get started

### 0. Authentication Setup (Private Repository Only)

**Note:** This step is only required when EvalKit is hosted in a private repository. 

#### GitHub Personal Access Token Setup

1. **Create a Personal Access Token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Select scopes: `repo` (full control of private repositories)
   - Copy the generated token

2. **Configure Git credentials:**
   ```bash
   # Add to your shell profile (~/.zshrc, ~/.bashrc, or ~/.bash_profile)
   export GITHUB_TOKEN="your_personal_access_token_here"
   
   # Reload your shell configuration
   source ~/.zshrc  # or source ~/.bashrc
   ```

### 1. Install EvalKit

Choose your preferred installation method:

#### Option 1: Persistent Installation (Recommended)

Install once and use everywhere:

```bash
uv tool install evalkit-cli --from git+https://github.com/kangISU/eval-kit.git
```

Then use the tool directly:

```bash
evalkit init <PROJECT_NAME>
evalkit check
```

To upgrade evalkit run:

```bash
uv tool install evalkit-cli --force --from git+https://github.com/kangISU/eval-kit.git
```

#### Option 2: One-time Usage

Run directly without installing:

```bash
uvx --from git+https://github.com/kangISU/eval-kit.git evalkit init <PROJECT_NAME>
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

### 3. Create evaluation implementation plan

Use the **`/evalkit.plan`** command to create technical implementation plans for your evaluation infrastructure.

```bash
/evalkit.plan Use DeepEval for metrics computation, implement real-time monitoring, and create interactive dashboards for result visualization
```

### 4. Implement evaluation pipeline

Use **`/evalkit.implement`** to build your evaluation pipeline according to the plan.

```bash
/evalkit.implement
```

### 5. Analyze results and get insights

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

# Initialize with PowerShell scripts (Windows/cross-platform, support soon)
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
| `/evalkit.plan`          | Create evaluation implementation plan                                  |
| `/evalkit.implement`     | Execute evaluation pipeline implementation                             |
| `/evalkit.insights`      | Analyze results and provide improvement suggestions                    |

### Environment Variables

| Variable         | Description                                                                                    |
|------------------|------------------------------------------------------------------------------------------------|
| `EVALKIT_FEATURE` | Override feature detection for non-Git repositories. Set to the feature directory name (e.g., `001-chatbot-evaluation`) to work on a specific evaluation when not using Git branches.<br/>**Must be set in the context of the agent you're working with prior to using `/evalkit.plan` or follow-up commands. |

## 🔧 Prerequisites

- **Linux/macOS** (or WSL2 on Windows)
- AI coding assistant: [Kilo Code](https://kilocode.ai), [Claude Code](https://www.anthropic.com/claude-code), or [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

If you encounter issues with an assistant, please open an issue so we can refine the integration.

---

## 👥 Maintainers

- Kang Zhou ([@kangISU](https://github.com/kangISU))

## 🙏 Acknowledgements

This project evolved from [spec-kit](https://github.com/github/spec-kit), transforming from a software development specification toolkit into a comprehensive agent evaluation framework.
