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
# Create demo project in your preferred location
cd /path/to/your/projects  # Choose your preferred directory
uv run python /path/to/eval-kit/src/evalkit_cli/__init__.py init demo-evaluation --ai kilocode --ignore-agent-tools --script sh
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
# Create demo project in your preferred location
cd /path/to/your/projects  # Choose your preferred directory
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

1. **Create test projects in your preferred location:**
   ```bash
   # Test your CLI changes in demo projects (uses isolated environment)
   # Navigate to your preferred directory for demo projects
   cd /path/to/your/projects  # e.g., ~/projects, /tmp, or same level as eval-kit
   evalkit init demo-evaluation --ai kilocode --ignore-agent-tools --script sh
   cd demo-evaluation
   code .
   # Test evalkit commands in your AI assistant (/evalkit.design, etc.)
   ```

2. **Testing template/script changes workflow:**
   ```bash
   # 1. Use --local-dev flag to test your current branch changes immediately
   # Navigate to your preferred directory for demo projects
   cd /path/to/your/projects
   evalkit init demo-evaluation --ai kilocode --local-dev --ignore-agent-tools --script sh
   cd demo-evaluation
   
   # 2. Test your changes - templates and scripts reflect your current branch
   # - Commands are in: .claude/commands/ or .kilocode/workflows/ or .amazonq/prompts/
   # - Templates are in: .evalkit/templates/
   # - Scripts are in: .evalkit/scripts/
   
   # 3. Make changes to templates/scripts in your main repo, then re-init to test
   cd /path/to/eval-kit  # Back to main repo
   # Edit files in templates/ or scripts/ directories
   # Re-initialize to test changes:
   cd /path/to/your/projects
   evalkit init demo-evaluation --ai kilocode --local-dev --ignore-agent-tools --script sh
   
   # 4. Commit changes when satisfied (from eval-kit directory)
   cd /path/to/eval-kit
   git add templates/ scripts/
   git commit -m "Update templates and scripts"
   ```

   **Alternative: Test build script directly**
   ```bash
   # You can also test the build process directly without creating a project
   .github/workflows/scripts/build-local-dev.sh kilocode sh
   # This creates processed templates in .genlocal/ directory for inspection
   ```

   **Key Benefits of Local Development Mode:**
   - ✅ **Immediate reflection**: Changes to `templates/` and `scripts/` are used instantly
   - ✅ **Proper processing**: Templates are processed with the same logic as GitHub releases
   - ✅ **Branch-aware**: Uses whatever templates/scripts are in your current working branch
   - ✅ **Faster iteration**: No need to manually copy files back and forth
   - ✅ **Consistent**: Identical transformation logic as production releases

   **How Local Development Mode Works:**
   The `--local-dev` flag triggers a local build process that:
   1. Runs [`.github/workflows/scripts/build-local-dev.sh`](../.github/workflows/scripts/build-local-dev.sh)
   2. Uses the same template processing logic as GitHub releases
   3. Processes templates (replaces `{SCRIPT}`, `{ARGS}`, etc. placeholders)
   4. Creates proper directory structure for your AI assistant
   5. Copies processed templates to your project directory

### Committing Changes

1. **Test thoroughly in demo projects first**
2. **Only commit CLI source code changes** (not demo projects)
3. **Push to feature branch, then merge to main**
4. **⚠️ IMPORTANT: Pushing to main triggers automatic release**
   - Changes to `templates/`, `scripts/`, `.github/workflows/` trigger release workflow
   - Template changes become available immediately after release completes
   - Test thoroughly before merging to main
