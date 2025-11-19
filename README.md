<div align="center">
    <h1>Agent-EvalKit</h1>
    <h3><em>Evaluate AI agents quickly</em></h3>
</div>

<p align="center">
    <strong>A toolkit for developers to quickly build trace-based evaluation pipelines with flexible evaluation SDK support.</strong>
</p>

---

## Table of Contents

- [⚡ Get started](#-get-started)
- [📋 What to Expect from EvalKit](#-what-to-expect-from-evalkit)
- [🤖 Supported AI Assistants](#-supported-ai-assistants)
- [📚 EvalKit Reference](#-evalkit-reference)
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

### 3. Build evaluation pipeline

Choose your approach based on your experience level:

#### Option A: Guided step-by-step workflow (recommended for first-time users)

Use **`/evalkit.quick`** for an interactive, step-by-step guide through the complete evaluation pipeline:

```bash
/evalkit.quick Evaluate my data analysis agent focusing on goal success
```

This will guide you through each step with confirmation prompts and progress tracking.

#### Option B: Individual commands (for experienced users)

Run each command individually for more control:

**Step 1: Design evaluation strategy**
```bash
/evalkit.plan Analyze my data analysis agent and design evaluation strategy focusing on goal success
```

**Step 2: Generate test cases** *(user input optional)*
```bash
/evalkit.data Generate test cases covering data analysis scenarios including edge cases
```

**Step 3: Set up tracing instrumentation** *(user input optional)*
```bash
/evalkit.trace Add Traceloop instrumentation to capture agent execution traces
```

**Step 4: Run agent and collect traces** *(user input optional)*
```bash
/evalkit.run_agent
```

**Step 5: Implement evaluation code** *(user input optional)*
```bash
/evalkit.eval
```

**Step 6: Analyze results and get recommendations** *(user input optional)*
```bash
/evalkit.report
```

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

### Next Steps for Developers

**EvalKit provides the educational foundation - you should:**
- **Review generated artifacts**: Examine all code, configurations, and evaluation logic
- **Customize metrics**: Update and refine evaluation metrics for your specific use case
- **Finalize implementation**: Enhance the basic working version for production requirements
- **Integrate with deployment**: Adapt the trace-based approach for your deployment monitoring if needed

EvalKit teaches you how to build trace-based evaluation pipelines with a working baseline that you can extend and customize for your specific agent evaluation needs.

## 🤖 Supported AI Assistants

| Assistant                                                     | Support | Notes                                             |
|---------------------------------------------------------------|---------|---------------------------------------------------|
| [Claude Code](https://www.anthropic.com/claude-code)         | ✅ |                                                   |
| [Kilo Code](https://kilocode.ai)                              | 🔄 | Support coming soon                           |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | 🔄 | Support coming soon                           |

## 📚 EvalKit Reference

The `evalkit` command supports the following options:

### Commands

| Command     | Description                                                    |
|-------------|----------------------------------------------------------------|
| `init`      | Initialize a new evaluation project from the latest template      |
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
evalkit init my-agent-evaluation --ai claude

# Initialize in current directory
evalkit init . --ai claude
# or use the --here flag
evalkit init --here --ai claude

# Force merge into current (non-empty) directory without confirmation
evalkit init . --force --ai claude
# or 
evalkit init --here --force --ai claude

# Skip git initialization
evalkit init my-agent-evaluation --ai claude --no-git

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
| `/evalkit.quick`         | Interactive step-by-step guide through complete evaluation pipeline  |
| `/evalkit.plan`          | Analyze agent and design trace-based evaluation strategy             |
| `/evalkit.data`          | Generate comprehensive test cases for evaluation scenarios            |
| `/evalkit.trace`         | Add tracing instrumentation to agent for trace-based evaluation      |
| `/evalkit.run_agent`     | Execute instrumented agent on test cases and collect traces          |
| `/evalkit.eval`          | Implement and execute evaluation code to compute metrics over traces |
| `/evalkit.report`        | Analyze results and provide actionable improvement recommendations    |


## 🔧 Prerequisites

- **Linux/macOS**
- AI coding assistant: [Claude Code](https://www.anthropic.com/claude-code), [Kilo Code](https://kilocode.ai), or [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

If you encounter issues with an assistant, please open an issue so we can refine the integration.

## 👨‍💻 For Developers

If you want to contribute to EvalKit, see the [Local Development Guide](./docs/local-development.md).

---

## 🙏 Acknowledgements

This project archecture is inspired by [spec-kit](https://github.com/github/spec-kit).
