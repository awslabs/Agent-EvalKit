# Installation Guide

## Prerequisites

- **Linux/macOS** (or Windows; PowerShell scripts now supported without WSL)
- AI coding assistant: [Kilo Code](https://kilocode.ai), [Claude Code](https://www.anthropic.com/claude-code), or [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## Installation

### Initialize a New Evaluation Project

The easiest way to get started is to initialize a new evaluation project:

```bash
uvx --from git+https://github.com/github/eval-kit.git evalkit init <PROJECT_NAME>
```

Or initialize in the current directory:

```bash
uvx --from git+https://github.com/github/eval-kit.git evalkit init .
# or use the --here flag
uvx --from git+https://github.com/github/eval-kit.git evalkit init --here
```

### Specify AI Assistant

You can proactively specify your AI assistant during initialization:

```bash
uvx --from git+https://github.com/github/eval-kit.git evalkit init <project_name> --ai kilocode
uvx --from git+https://github.com/github/eval-kit.git evalkit init <project_name> --ai claude
uvx --from git+https://github.com/github/eval-kit.git evalkit init <project_name> --ai q
```

### Specify Script Type (Shell vs PowerShell)

All automation scripts now have both Bash (`.sh`) and PowerShell (`.ps1`) variants.

Auto behavior:
- Windows default: `ps`
- Other OS default: `sh`
- Interactive mode: you'll be prompted unless you pass `--script`

Force a specific script type:
```bash
uvx --from git+https://github.com/github/eval-kit.git evalkit init <project_name> --script sh
uvx --from git+https://github.com/github/eval-kit.git evalkit init <project_name> --script ps
```

### Ignore Agent Tools Check

If you prefer to get the templates without checking for the right tools:

```bash
uvx --from git+https://github.com/github/eval-kit.git evalkit init <project_name> --ai claude --ignore-agent-tools
```

## Verification

After initialization, you should see the following commands available in your AI assistant:
- `/evalkit.design` - Analyze agent and design evaluation strategy
- `/evalkit.clarify` - Clarify evaluation requirements (optional)
- `/evalkit.plan` - Create evaluation implementation plan
- `/evalkit.tasks` - Generate evaluation task lists
- `/evalkit.implement` - Execute evaluation pipeline implementation
- `/evalkit.insights` - Analyze results and provide improvement suggestions

The evaluation project directory will contain both `.sh` and `.ps1` scripts for cross-platform support.

## Troubleshooting

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
