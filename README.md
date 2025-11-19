<div align="center">
    <h1>Agent-EvalKit</h1>
    <h3><em>Evaluate AI agents quickly</em></h3>
</div>

<p align="center">
    <strong>A toolkit for developers to quickly build agent evaluation pipelines with flexible evaluation SDK support.</strong>
</p>

---

## Table of Contents

- [⚡ Get started](#-get-started)
- [📋 What to Expect from EvalKit](#-what-to-expect-from-evalkit)
- [🤖 Supported AI Assistants](#-supported-ai-assistants)
- [🔧 EvalKit CLI Reference](#-evalkit-cli-reference)
- [🔧 Prerequisites](#-prerequisites)
- [👨‍💻 For Developers](#-for-developers)
- [🙏 Acknowledgements](#-acknowledgements)

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

Install once and use everywhere:

```bash
uv tool install evalkit --from git+https://github.com/awslabs/Agent-EvalKit.git
```

To upgrade evalkit later:

```bash
uv tool install evalkit --force --from git+https://github.com/awslabs/Agent-EvalKit.git
```

To uninstall evalkit:

```bash
uv tool uninstall evalkit
```

### 2. Best Practices: Before You Start

#### 2.1 Ensure Agent Readiness

**EvalKit requires your agent to be fully runnable with all dependencies and API keys available locally.** Our evaluation framework expects real agent behavior without mocking any components, as intermediate steps may require the agent to generate artifacts for following evaluation phases (such as generating execution traces).

**Before starting the evaluation workflow, ensure:**
- Your agent runs successfully in your local environment
- All required dependencies are documented (e.g., in a `requirements.txt`)
- API keys and credentials are properly set up (e.g., `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)

#### 2.2 Set Up Dedicated Evaluation Project

**Create a dedicated evaluation project to keep your agent code separate from evaluation artifacts.**

```bash
# Create and initialize a new evaluation project
evalkit init my-agent-evaluation
cd my-agent-evaluation

# Copy your agent folder into the evaluation project
cp -r /path/to/your/agent-folder .
# This ensures the evaluation project can easily access your agent code
```

#### Why These Practices Matter

These requirements are essential because EvalKit's trace-based evaluation approach captures actual agent execution patterns and behaviors for comprehensive analysis. The dedicated project structure:

- Protects your original agent code by working with a copy that's safe to modify
- Makes it easier to manage evaluation-specific dependencies and configurations
- Ensures reliable path resolution and artifact management throughout the evaluation process

### 3. Design evaluation strategy

Use the **`/evalkit.plan`** command to analyze your agent and design a comprehensive evaluation strategy with trace-based evaluation architecture. **User input is required** to specify your evaluation goals.

```bash
/evalkit.plan Analyze my customer service chatbot agent and design evaluation strategy focusing on response accuracy, latency, and user satisfaction
```

### 4. Generate test cases (if needed)

Use **`/evalkit.data`** to generate comprehensive test cases for your evaluation scenarios. **User input is optional** - the command will use design specifications if no input provided.

```bash
/evalkit.data Generate test cases covering customer service scenarios including edge cases
```

Or simply:
```bash
/evalkit.data
```

### 5. Set up tracing instrumentation (if needed)

Use **`/evalkit.trace`** to add tracing instrumentation to your agent for trace-based evaluation. **User input is optional** - the command will use design specifications if no input provided.

```bash
/evalkit.trace Add Traceloop instrumentation to capture agent execution traces
```

Or simply:
```bash
/evalkit.trace
```

### 6. Implement evaluation pipeline

Use **`/evalkit.code`** to build your trace-based evaluation pipeline with normalized trace processing. **User input is optional** - the command will follow the established design and prerequisites.

```bash
/evalkit.code
```

### 7. Analyze results and get actionable recommendations (if needed)

Use **`/evalkit.report`** to analyze evaluation results and get actionable improvement recommendations. **User input is optional** - the command will analyze available results.

```bash
/evalkit.report
```

For detailed step-by-step instructions, see our [comprehensive guide](./docs/quickstart.md).

## 📋 What to Expect from EvalKit

**EvalKit provides a foundational trace-based evaluation pipeline designed for educational purposes and deployment alignment.**

### Output Deliverables

After completing the EvalKit workflow, you will have:

- **Local trace-based evaluation pipeline**: A working evaluation system that processes agent execution traces
- **Reusable evaluation metrics**: Trace-based metrics that can be directly applied in production deployment monitoring
- **Basic working implementation**: Functional code that demonstrates trace-based evaluation concepts and patterns

### Deployment Alignment

The evaluation metrics generated by EvalKit are designed to align with deployment phase monitoring:
- **Trace compatibility**: Metrics take traces as input, matching production trace generation
- **Monitoring ready**: Same evaluation logic can be used for ongoing agent performance monitoring
- **Scalable foundation**: Architecture supports extension for production-scale evaluation needs

### Next Steps for Developers

**EvalKit provides the educational foundation - you should:**
- **Review generated artifacts**: Examine all code, configurations, and evaluation logic
- **Customize metrics**: Update and refine evaluation metrics for your specific use case
- **Finalize implementation**: Enhance the basic working version for production requirements
- **Integrate with deployment**: Adapt the trace-based approach for your deployment monitoring

EvalKit teaches you how to build trace-based evaluation pipelines with a working baseline that you can extend and customize for your specific agent evaluation needs.

## 🤖 Supported AI Assistants

| Assistant                                                     | Support | Notes                                             |
|---------------------------------------------------------------|---------|---------------------------------------------------|
| [Claude Code](https://www.anthropic.com/claude-code)         | ✅ |                                                   |
| [Kilo Code](https://kilocode.ai)                              | 🔄 | CLI support coming soon                           |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | 🔄 | CLI support coming soon                           |

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
evalkit init my-evaluation --ai claude

# Initialize in current directory
evalkit init . --ai claude
# or use the --here flag
evalkit init --here --ai claude

# Force merge into current (non-empty) directory without confirmation
evalkit init . --force --ai claude
# or 
evalkit init --here --force --ai claude

# Skip git initialization
evalkit init my-evaluation --ai claude --no-git

# Enable debug output for troubleshooting
evalkit init my-agent-evaluation --ai claude --debug

# Use GitHub token for API requests (helpful for corporate environments)
evalkit init my-agent-evaluation --ai claude --github-token ghp_your_token_here

# Check system requirements
evalkit check
```

### Available Slash Commands

After running `evalkit init`, your AI coding assistant will have access to these slash commands for structured agent evaluation:

#### Core Commands

Essential commands for the trace-based Agent Evaluation workflow:

| Command                  | Description                                                           |
|--------------------------|-----------------------------------------------------------------------|
| `/evalkit.plan`          | Analyze agent and design trace-based evaluation strategy             |
| `/evalkit.data`          | Generate comprehensive test cases for evaluation scenarios            |
| `/evalkit.trace`         | Add tracing instrumentation to agent for trace-based evaluation      |
| `/evalkit.code`          | Execute trace-based evaluation pipeline implementation                |
| `/evalkit.report`        | Analyze results and provide actionable improvement recommendations    |

### Environment Variables

| Variable         | Description                                                                                    |
|------------------|------------------------------------------------------------------------------------------------|
| `EVALKIT_FEATURE` | Override feature detection for non-Git repositories. Set to the feature directory name (e.g., `001-chatbot-evaluation`) to work on a specific evaluation when not using Git branches.<br/>**Must be set in the context of the agent you're working with prior to using `/evalkit.plan` or follow-up commands. |

## 🔧 Prerequisites

- **Linux/macOS** (or WSL2 on Windows)
- AI coding assistant: [Claude Code](https://www.anthropic.com/claude-code), [Kilo Code](https://kilocode.ai), or [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

If you encounter issues with an assistant, please open an issue so we can refine the integration.

## 👨‍💻 For Developers

If you want to contribute to EvalKit or modify templates/scripts, see the [Local Development Guide](./docs/local-development.md) for:

- Authentication setup for private repository access
- CLI development workflow and testing
- Template/script modification workflow
- Release process and best practices

---

## 🙏 Acknowledgements

This project archecture is inspired by [spec-kit](https://github.com/github/spec-kit).
