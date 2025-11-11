# Local Development Guide

This guide shows how to develop and test EvalKit changes locally without publishing releases.

## 0. Authentication Setup

Since EvalKit is in a private repository, configure Git authentication first.

### GitHub Personal Access Token

1. **Create token**: GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Select scope: `repo` (full control of private repositories)
   - Copy the generated token

2. **Configure credentials**:
   ```bash
   # Add to shell profile (~/.zshrc, ~/.bashrc, or ~/.bash_profile)
   export GITHUB_TOKEN="your_personal_access_token_here"
   
   # Reload configuration
   source ~/.zshrc  # or source ~/.bashrc
   ```

## 1. Setup Development Environment

```bash
# Clone and create feature branch
git clone https://github.com/kangISU/eval-kit.git
cd eval-kit
git checkout -b your-feature-branch

# Create isolated environment
uv venv
source .venv/bin/activate

# Install in editable mode
uv pip install -e .

# Verify installation
evalkit --help
```

## 2. Claude Code Setup

Configure Claude Code for testing EvalKit commands:

**~/.claude/settings.json**:
```json
{
  "env": {
    "AWS_PROFILE": "claude",
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "DISABLE_PROMPT_CACHING": "1",
    "DISABLE_TELEMETRY": "1",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
  },
  "model": "us.anthropic.claude-sonnet-4-20250514-v1:0"
}
```

**~/.aws/config**:
```ini
[profile claude]
credential_process=/Users/<username>/.toolbox/bin/ada credentials print --profile=claude
region=us-west-2
account=<aws-account-number>
role=Admin
```

**Authentication**: Run `mwinit` then type `claude` in terminal to start Claude Code.

## 3. Development Workflow

### Test Changes Locally

1. **Create test project**:
   ```bash
   cd /path/to/your/workspace
   evalkit init demo-evaluation --ai claude --ignore-agent-tools --script sh --local-dev
   cd demo-evaluation
   code .
   ```

2. **Add your test agent**: Copy your agent folder to the demo project root directory.

3. **Test EvalKit commands**: Use `/evalkit.plan`, `/evalkit.trace`, etc. in Claude Code terminal.

### Iterate on Changes

1. **Make changes** to templates or scripts in your eval-kit repository
2. **Re-initialize** to test changes:
   ```bash
   cd /path/to/your/workspace
   evalkit init demo-evaluation --ai claude --ignore-agent-tools --script sh --local-dev
   # Or create new project:
   evalkit init demo-evaluation-2 --ai claude --ignore-agent-tools --script sh --local-dev
   ```
3. **Test updated commands** in VS Code with Claude Code

### Local Development Mode

The `--local-dev` flag:
- Uses your current branch's templates and scripts
- Processes templates with the same logic as GitHub releases  
- Updates `.claude/`, `.evalkit/`, and `.mcp.json` files
- Enables immediate testing of changes

## 4. Commit Process

1. **Test thoroughly** in demo projects
2. **Commit changes**:
   ```bash
   cd /path/to/eval-kit
   git add templates/ scripts/
   git commit -m "Update templates and scripts"
   ```
3. **Push to feature branch**, then merge to main

⚠️ **Important**: Pushing to main triggers automatic release. Test thoroughly before merging.
