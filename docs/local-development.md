# Local Development Guide

This guide shows how to iterate on the `evalkit` CLI locally without publishing a release or committing to `main` first.


## 0. Authentication Setup for Private Repository

Since EvalKit is hosted in a private repository, you need to configure Git authentication before installation.

### GitHub Personal Access Token Setup

1. **Create a Personal Access Token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Select scopes: `repo` (full control of private repositories)
   - Copy the generated token

2. **Configure Git credentials:**
   ```bash
   # Set up Git credential helper (one-time setup)
   git config --global credential.helper store
   
   # Clone any private repo to trigger credential prompt
   git clone https://github.com/kangISU/eval-kit.git temp-repo
   # Enter your GitHub username and the token as password
   rm -rf temp-repo
   ```

## 1. Clone and Switch Branches

```bash
git clone https://github.com/kangISU/eval-kit.git
cd eval-kit
# Work on a feature branch
git checkout -b your-feature-branch
```

## 2. Run the CLI Directly (Recommended: Use Editable Install)

For the best development experience, use the editable install method (see section 3 below). The CLI is configured as a script entry point, so you can't run it as a module with `python -m`.

If you need to run the CLI directly for debugging, use the script file:

```bash
# Run the script file directly
uv run python src/evalkit_cli/__init__.py --help
uv run python src/evalkit_cli/__init__.py init demo-evaluation --ai kilocode --ignore-agent-tools --script sh
cd demo-evaluation
# Start a new VS Code window
code .
# evalkit commands will be available in Kilo Code (by typing /evalkit.design.md)
```

## 3. Use Editable Install (Isolated Environment)

Create an isolated environment using `uv` so dependencies resolve exactly like end users get them:

```bash
# Create & activate virtual env (uv auto-manages .venv)
uv venv
source .venv/bin/activate  # or on Windows PowerShell: .venv\Scripts\Activate.ps1

# Install project in editable mode
uv pip install -e .

# Now 'evalkit' entrypoint is available
evalkit --help
evalkit init demo-evaluation --ai kilocode --ignore-agent-tools --script sh
cd demo-evaluation
# Start a new VS Code window
code .
# evalkit commands will be available in Kilo Code (by typing /evalkit.design.md)
```

Re-running after code edits requires no reinstall because of editable mode.

## Development Workflow

When developing EvalKit CLI features, follow this workflow to avoid polluting the main repository:

### Testing Changes Locally

1. **Create test projects in temporary directories:**
   ```bash
   # Test your CLI changes in demo projects (uses isolated environment)
   evalkit init demo-evaluation --ai kilocode --ignore-agent-tools
   cd demo-evaluation
   code .
   # Test evalkit commands in your AI assistant (/evalkit.design, etc.)
   ```

2. **Do NOT push demo projects to remote:**
   - Demo evaluation projects are for local testing only
   - Add demo projects to `.gitignore` or create them outside the repo
   - Only commit changes to the EvalKit CLI source code

3. **Testing template/script changes workflow:**
   ```bash
   # 1. Create demo project from current branch (main or your feature branch)
   evalkit init demo-evaluation --ai kilocode --ignore-agent-tools
   cd demo-evaluation
   
   # 2. Edit files directly in demo project for testing:
   # - Commands: .claude/commands/ or .kilocode/workflows/ or .amazonq/prompts/
   # - Templates: .evalkit/templates/
   # - Scripts: .evalkit/scripts/
   # Test and iterate until changes work well
   
   # 3. Copy working changes back to your feature branch
   cd ../  # Back to main repo
   cp -r demo-evaluation/.evalkit/templates/* templates/
   cp -r demo-evaluation/.evalkit/scripts/* scripts/
   cp -r demo-evaluation/.claude/commands/* templates/commands/  # if using Claude
   cp -r demo-evaluation/.kilocode/workflows/* templates/commands/  # if using Kilo Code
   cp -r demo-evaluation/.amazonq/prompts/* templates/commands/  # if using Amazon Q
   
   # 4. Commit changes to your feature branch, then PR to main
   git add templates/ scripts/
   git commit -m "Update templates and scripts"
   ```

### Committing Changes

1. **Test thoroughly in demo projects first**
2. **Only commit CLI source code changes** (not demo projects)
3. **Push to feature branch, then merge to main**
4. **⚠️ IMPORTANT: Pushing to main triggers automatic release**
   - Changes to `templates/`, `scripts/`, `.github/workflows/` trigger release workflow
   - Template changes become available immediately after release completes
   - Test thoroughly before merging to main
