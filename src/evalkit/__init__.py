#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "readchar",
#     "httpx",
# ]
# ///
"""
EvalKit - Evaluate AI agents quickly

Usage:
    uvx evalkit init <project-name>
    uvx evalkit init .
    uvx evalkit init --here

Or install globally:
    uv tool install evalkit
    evalkit init <project-name>
    evalkit init .
    evalkit init --here
"""

import os
import subprocess
import sys
import zipfile
import tempfile
import shutil
import shlex
from pathlib import Path
from typing import Optional, Tuple

import typer
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.table import Table
from rich.tree import Tree
from typer.core import TyperGroup

# For cross-platform keyboard input
import readchar
import ssl
import truststore

ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
client = httpx.Client(verify=ssl_context)


def _github_token(cli_token: str | None = None) -> str | None:
    """Return sanitized GitHub token (cli arg takes precedence) or None."""
    return ((cli_token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or "").strip()) or None


def _github_auth_headers(cli_token: str | None = None) -> dict:
    """Return Authorization header dict only when a non-empty token exists."""
    token = _github_token(cli_token)
    return {"Authorization": f"Bearer {token}"} if token else {}


# Agent configuration with name, folder, install URL, and CLI tool requirement
AGENT_CONFIG = {
    "claude": {
        "name": "Claude Code",
        "folder": ".claude/",
        "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",
        "requires_cli": True,
    },
    "kilocode": {
        "name": "Kilo Code (support soon)",
        "folder": ".kilocode/",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "q": {
        "name": "Amazon Q Developer CLI (support soon)",
        "folder": ".amazonq/",
        "install_url": "https://aws.amazon.com/developer/learning/q-developer-cli/",
        "requires_cli": True,
    },
}

SCRIPT_TYPE_CHOICES = {"sh": "POSIX Shell (bash/zsh)", "ps": "PowerShell (support soon)"}

CLAUDE_LOCAL_PATH = Path.home() / ".claude" / "local" / "claude"

BANNER = """
███████╗██╗   ██╗ █████╗ ██╗     ██╗  ██╗██╗████████╗
██╔════╝██║   ██║██╔══██╗██║     ██║ ██╔╝██║╚══██╔══╝
█████╗  ██║   ██║███████║██║     █████╔╝ ██║   ██║
██╔══╝  ╚██╗ ██╔╝██╔══██║██║     ██╔═██╗ ██║   ██║
███████╗ ╚████╔╝ ██║  ██║███████╗██║  ██╗██║   ██║
╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝
"""

TAGLINE = "EvalKit - Agent Evaluation Tool Kit"


class StepTracker:
    """Track and render hierarchical steps without emojis, similar to Claude Code tree output.
    Supports live auto-refresh via an attached refresh callback.
    """

    def __init__(self, title: str):
        self.title = title
        self.steps = []  # list of dicts: {key, label, status, detail}
        self.status_order = {"pending": 0, "running": 1, "done": 2, "error": 3, "skipped": 4}
        self._refresh_cb = None  # callable to trigger UI refresh

    def attach_refresh(self, cb):
        self._refresh_cb = cb

    def add(self, key: str, label: str):
        if key not in [s["key"] for s in self.steps]:
            self.steps.append({"key": key, "label": label, "status": "pending", "detail": ""})
            self._maybe_refresh()

    def start(self, key: str, detail: str = ""):
        self._update(key, status="running", detail=detail)

    def complete(self, key: str, detail: str = ""):
        self._update(key, status="done", detail=detail)

    def error(self, key: str, detail: str = ""):
        self._update(key, status="error", detail=detail)

    def skip(self, key: str, detail: str = ""):
        self._update(key, status="skipped", detail=detail)

    def _update(self, key: str, status: str, detail: str):
        for s in self.steps:
            if s["key"] == key:
                s["status"] = status
                if detail:
                    s["detail"] = detail
                self._maybe_refresh()
                return

        self.steps.append({"key": key, "label": key, "status": status, "detail": detail})
        self._maybe_refresh()

    def _maybe_refresh(self):
        if self._refresh_cb:
            try:
                self._refresh_cb()
            except Exception:
                pass

    def render(self):
        tree = Tree(f"[cyan]{self.title}[/cyan]", guide_style="grey50")
        for step in self.steps:
            label = step["label"]
            detail_text = step["detail"].strip() if step["detail"] else ""

            status = step["status"]
            if status == "done":
                symbol = "[green]●[/green]"
            elif status == "pending":
                symbol = "[green dim]○[/green dim]"
            elif status == "running":
                symbol = "[cyan]○[/cyan]"
            elif status == "error":
                symbol = "[red]●[/red]"
            elif status == "skipped":
                symbol = "[yellow]○[/yellow]"
            else:
                symbol = " "

            if status == "pending":
                # Entire line light gray (pending)
                if detail_text:
                    line = f"{symbol} [bright_black]{label} ({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [bright_black]{label}[/bright_black]"
            else:
                # Label white, detail (if any) light gray in parentheses
                if detail_text:
                    line = f"{symbol} [white]{label}[/white] [bright_black]({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [white]{label}[/white]"

            tree.add(line)
        return tree


def get_key():
    """Get a single keypress in a cross-platform way using readchar."""
    key = readchar.readkey()

    if key == readchar.key.UP or key == readchar.key.CTRL_P:
        return "up"
    if key == readchar.key.DOWN or key == readchar.key.CTRL_N:
        return "down"

    if key == readchar.key.ENTER:
        return "enter"

    # Handle escape key - works with double escape press
    if key == readchar.key.ESC or key == "\x1b\x1b":
        return "escape"

    if key == readchar.key.CTRL_C:
        raise KeyboardInterrupt

    return key


def select_with_arrows(options: dict, prompt_text: str = "Select an option", default_key: str = None) -> str:
    """
    Interactive selection using arrow keys with Rich Live display.

    Args:
        options: Dict with keys as option keys and values as descriptions
        prompt_text: Text to show above the options
        default_key: Default option key to start with

    Returns:
        Selected option key
    """
    option_keys = list(options.keys())
    if default_key and default_key in option_keys:
        selected_index = option_keys.index(default_key)
    else:
        selected_index = 0

    selected_key = None

    def create_selection_panel():
        """Create the selection panel with current selection highlighted."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="left", width=3)
        table.add_column(style="white", justify="left")

        for i, key in enumerate(option_keys):
            if i == selected_index:
                table.add_row("▶", f"[cyan]{key}[/cyan] [dim]- {options[key]}[/dim]")
            else:
                table.add_row(" ", f"[cyan]{key}[/cyan] [dim]- {options[key]}[/dim]")

        table.add_row("", "")
        table.add_row("", "[dim]Use ↑/↓ to navigate, Enter to select, Ctrl+C to cancel[/dim]")

        return Panel(table, title=f"[bold]{prompt_text}[/bold]", border_style="cyan", padding=(1, 2))

    console.print()

    def run_selection_loop():
        nonlocal selected_key, selected_index
        with Live(create_selection_panel(), console=console, transient=True, auto_refresh=False) as live:
            while True:
                try:
                    key = get_key()
                    if key == "up":
                        selected_index = (selected_index - 1) % len(option_keys)
                    elif key == "down":
                        selected_index = (selected_index + 1) % len(option_keys)
                    elif key == "enter":
                        selected_key = option_keys[selected_index]
                        break
                    elif key == "escape":
                        console.print("\n[yellow]Selection cancelled[/yellow]")
                        raise typer.Exit(1)

                    live.update(create_selection_panel(), refresh=True)

                except KeyboardInterrupt:
                    console.print("\n[yellow]Selection cancelled[/yellow]")
                    raise typer.Exit(1)

    run_selection_loop()

    if selected_key is None:
        console.print("\n[red]Selection failed.[/red]")
        raise typer.Exit(1)

    return selected_key


console = Console()


class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""

    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)


app = typer.Typer(
    name="evalkit",
    help="Setup tool for EvalKit agent evaluation projects",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)


def show_banner():
    """Display the ASCII art banner."""
    banner_lines = BANNER.strip().split("\n")
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]

    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)

    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()


@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]Run 'evalkit --help' for usage information[/dim]"))
        console.print()


def run_command(cmd: list[str], check_return: bool = True, capture: bool = False, shell: bool = False) -> Optional[str]:
    """Run a shell command and optionally capture output."""
    try:
        if capture:
            result = subprocess.run(cmd, check=check_return, capture_output=True, text=True, shell=shell)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check_return, shell=shell)
            return None
    except subprocess.CalledProcessError as e:
        if check_return:
            console.print(f"[red]Error running command:[/red] {' '.join(cmd)}")
            console.print(f"[red]Exit code:[/red] {e.returncode}")
            if hasattr(e, "stderr") and e.stderr:
                console.print(f"[red]Error output:[/red] {e.stderr}")
            raise
        return None


def check_tool(tool: str, tracker: StepTracker = None) -> bool:
    """Check if a tool is installed. Optionally update tracker.

    Args:
        tool: Name of the tool to check
        tracker: Optional StepTracker to update with results

    Returns:
        True if tool is found, False otherwise
    """
    # Special handling for Claude CLI after `claude migrate-installer`
    # See: https://github.com/github/spec-kit/issues/123
    # The migrate-installer command REMOVES the original executable from PATH
    # and creates an alias at ~/.claude/local/claude instead
    # This path should be prioritized over other claude executables in PATH
    if tool == "claude":
        if CLAUDE_LOCAL_PATH.exists() and CLAUDE_LOCAL_PATH.is_file():
            if tracker:
                tracker.complete(tool, "available")
            return True

    found = shutil.which(tool) is not None

    if tracker:
        if found:
            tracker.complete(tool, "available")
        else:
            tracker.error(tool, "not found")

    return found


def is_git_repo(path: Path = None) -> bool:
    """Check if the specified path is inside a git repository."""
    if path is None:
        path = Path.cwd()

    if not path.is_dir():
        return False

    try:
        # Use git command to check if inside a work tree
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
            cwd=path,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def init_git_repo(project_path: Path, quiet: bool = False) -> Tuple[bool, Optional[str]]:
    """Initialize a git repository in the specified path.

    Args:
        project_path: Path to initialize git repository in
        quiet: if True suppress console output (tracker handles status)

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        original_cwd = Path.cwd()
        os.chdir(project_path)
        if not quiet:
            console.print("[cyan]Initializing git repository...[/cyan]")
        subprocess.run(["git", "init"], check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit from EvalKit template"], check=True, capture_output=True, text=True
        )
        if not quiet:
            console.print("[green]✓[/green] Git repository initialized")
        return True, None

    except subprocess.CalledProcessError as e:
        error_msg = f"Command: {' '.join(e.cmd)}\nExit code: {e.returncode}"
        if e.stderr:
            error_msg += f"\nError: {e.stderr.strip()}"
        elif e.stdout:
            error_msg += f"\nOutput: {e.stdout.strip()}"

        if not quiet:
            console.print(f"[red]Error initializing git repository:[/red] {e}")
        return False, error_msg
    finally:
        os.chdir(original_cwd)


def download_template_from_github(
    ai_assistant: str,
    download_dir: Path,
    *,
    script_type: str = "sh",
    verbose: bool = True,
    show_progress: bool = True,
    client: httpx.Client = None,
    debug: bool = False,
    github_token: str = None,
) -> Tuple[Path, dict]:
    repo_owner = "awslabs"  # Replace with your GitHub username
    repo_name = "Agent-EvalKit"  # Your repository name
    if client is None:
        client = httpx.Client(verify=ssl_context)

    if verbose:
        console.print("[cyan]Fetching latest release information...[/cyan]")
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    try:
        response = client.get(
            api_url,
            timeout=30,
            follow_redirects=True,
            headers=_github_auth_headers(github_token),
        )
        status = response.status_code
        if status != 200:
            msg = f"GitHub API returned {status} for {api_url}"
            if debug:
                msg += f"\nResponse headers: {response.headers}\nBody (truncated 500): {response.text[:500]}"
            raise RuntimeError(msg)
        try:
            release_data = response.json()
        except ValueError as je:
            raise RuntimeError(f"Failed to parse release JSON: {je}\nRaw (truncated 400): {response.text[:400]}")
    except Exception as e:
        console.print("[red]Error fetching release information[/red]")
        console.print(Panel(str(e), title="Fetch Error", border_style="red"))
        raise typer.Exit(1)

    assets = release_data.get("assets", [])
    pattern = f"evalkit-template-{ai_assistant}-{script_type}"
    # Match assets that start with the pattern and end with .zip, allowing for version suffixes
    matching_assets = [
        asset for asset in assets if asset["name"].startswith(pattern) and asset["name"].endswith(".zip")
    ]

    asset = matching_assets[0] if matching_assets else None

    if asset is None:
        console.print(
            f"[red]No matching release asset found[/red] for [bold]{ai_assistant}[/bold] (expected pattern: [bold]{pattern}[/bold])"
        )
        asset_names = [a.get("name", "?") for a in assets]
        console.print(Panel("\n".join(asset_names) or "(no assets)", title="Available Assets", border_style="yellow"))
        raise typer.Exit(1)

    browser_download_url = asset["browser_download_url"]
    api_download_url = asset["url"]
    filename = asset["name"]
    file_size = asset["size"]

    if verbose:
        console.print(f"[cyan]Found template:[/cyan] {filename}")
        console.print(f"[cyan]Size:[/cyan] {file_size:,} bytes")
        console.print(f"[cyan]Release:[/cyan] {release_data['tag_name']}")

    zip_path = download_dir / filename
    if verbose:
        console.print("[cyan]Downloading template...[/cyan]")

    # Try browser download URL first (works for public repos), then fall back to API (for private repos)
    download_attempts = [
        (browser_download_url, _github_auth_headers(github_token)),
        (api_download_url, {**_github_auth_headers(github_token), "Accept": "application/octet-stream"}),
    ]

    last_error = None
    try:
        for attempt_num, (download_url, headers) in enumerate(download_attempts, 1):
            try:
                with client.stream(
                    "GET",
                    download_url,
                    timeout=60,
                    follow_redirects=True,
                    headers=headers,
                ) as response:
                    if response.status_code != 200:
                        # If first attempt fails, try the second one
                        if attempt_num == 1:
                            if debug:
                                console.print(
                                    f"[yellow]Browser download failed ({response.status_code}), trying API endpoint...[/yellow]"
                                )
                            continue

                        # Read the response content first for error reporting
                        try:
                            body_sample = ""
                            for chunk in response.iter_bytes(chunk_size=400):
                                body_sample += chunk.decode("utf-8", errors="ignore")
                                break  # Only read first chunk for error message
                        except Exception:
                            body_sample = "(unable to read response body)"
                        raise RuntimeError(
                            f"Download failed with {response.status_code}\n"
                            f"Headers: {response.headers}\nBody (truncated): {body_sample}"
                        )

                    # Success! Continue with download inside this response context
                    total_size = int(response.headers.get("content-length", 0))
                    with open(zip_path, "wb") as f:
                        if total_size == 0:
                            for chunk in response.iter_bytes(chunk_size=8192):
                                f.write(chunk)
                        else:
                            if show_progress:
                                with Progress(
                                    SpinnerColumn(),
                                    TextColumn("[progress.description]{task.description}"),
                                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                                    console=console,
                                ) as progress:
                                    task = progress.add_task("Downloading...", total=total_size)
                                    downloaded = 0
                                    for chunk in response.iter_bytes(chunk_size=8192):
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        progress.update(task, completed=downloaded)
                            else:
                                for chunk in response.iter_bytes(chunk_size=8192):
                                    f.write(chunk)
                    # Download completed successfully, break out of attempt loop
                    break
            except Exception as e:
                last_error = e
                if attempt_num == 1:
                    if debug:
                        console.print(f"[yellow]Browser download failed: {e}, trying API endpoint...[/yellow]")
                    continue
                else:
                    # Both attempts failed, re-raise the last error
                    if debug:
                        console.print(f"[red]API endpoint also failed: {e}[/red]")
                    raise
        else:
            # This should not happen, but just in case
            if last_error:
                raise last_error
            raise RuntimeError("All download attempts failed")
    except Exception as e:
        error_msg = f"Error downloading template: {e}"
        if debug:
            console.print(f"[red]{error_msg}[/red]")
            import traceback

            console.print(f"[red]Traceback:[/red] {traceback.format_exc()}")
        else:
            console.print(f"[red]Error downloading template[/red]")

        if zip_path.exists():
            zip_path.unlink()
        console.print(Panel(str(e), title="Download Error", border_style="red"))
        raise typer.Exit(1)

    if verbose:
        console.print(f"Downloaded: {filename}")
    metadata = {"filename": filename, "size": file_size, "release": release_data["tag_name"], "asset_url": download_url}
    return zip_path, metadata


def copy_local_template(
    project_path: Path,
    ai_assistant: str,
    script_type: str,
    is_current_dir: bool = False,
    *,
    verbose: bool = True,
    tracker: StepTracker | None = None,
    debug: bool = False,
) -> Path:
    """Build and copy templates from local directories using the same process as releases.

    This function:
    1. Runs the local development build script to process templates
    2. Copies the processed templates to the target project directory
    3. Uses the exact same transformation logic as GitHub releases

    Args:
        project_path: Target directory for the project
        ai_assistant: AI assistant type (kilocode, claude, q)
        script_type: Script type (sh, ps)
        is_current_dir: Whether initializing in current directory
        verbose: Whether to show verbose output
        tracker: Optional progress tracker
        debug: Whether to show debug information

    Returns:
        Path to the created project directory
    """
    # Get repo root directory (where this CLI script is located)
    repo_root = Path(__file__).parent.parent.parent
    genlocal_dir = repo_root / ".genlocal"

    if tracker:
        tracker.start("local-build", f"building {ai_assistant} ({script_type}) templates")
    elif verbose:
        console.print(f"[cyan]Building local templates for {ai_assistant} ({script_type})...[/cyan]")

    # Run the local development build script
    build_script = repo_root / ".github" / "workflows" / "scripts" / "build-local-dev.sh"

    try:
        # Execute the build script with the specified agent and script type
        result = subprocess.run(
            [str(build_script), ai_assistant, script_type],
            check=True,
            cwd=repo_root,
            capture_output=not debug,  # Show output in debug mode
            text=True,
        )

        if debug and result.stdout:
            console.print(f"[dim]Build output: {result.stdout}[/dim]")

    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to build local development package: {e}"
        if debug and e.stderr:
            error_msg += f"\nBuild error: {e.stderr}"
        if tracker:
            tracker.error("local-build", error_msg)
        raise RuntimeError(error_msg)

    if tracker:
        tracker.complete("local-build", "templates processed")
        tracker.add("local-copy", "Copy processed templates")
        tracker.start("local-copy")
    elif verbose:
        console.print("[cyan]Copying processed templates...[/cyan]")

    # Find the built package directory
    package_dir = genlocal_dir / f"evalkit-{ai_assistant}-package-{script_type}"

    if not package_dir.exists():
        error_msg = f"Local package not found: {package_dir}"
        if tracker:
            tracker.error("local-copy", error_msg)
        raise RuntimeError(error_msg)

    try:
        # Copy the built package to the target location
        if is_current_dir:
            # Merge into current directory (same logic as GitHub download)
            for item in package_dir.iterdir():
                dest_path = project_path / item.name
                if item.is_dir():
                    if dest_path.exists():
                        # Merge directories recursively
                        if verbose and not tracker:
                            console.print(f"[yellow]Merging directory:[/yellow] {item.name}")
                        for sub_item in item.rglob("*"):
                            if sub_item.is_file():
                                rel_path = sub_item.relative_to(item)
                                dest_file = dest_path / rel_path
                                dest_file.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(sub_item, dest_file)
                    else:
                        shutil.copytree(item, dest_path)
                else:
                    if dest_path.exists() and verbose and not tracker:
                        console.print(f"[yellow]Overwriting file:[/yellow] {item.name}")
                    shutil.copy2(item, dest_path)
            if verbose and not tracker:
                console.print("[cyan]Local templates merged into current directory[/cyan]")
        else:
            # Copy entire package to new directory
            if not project_path.exists():
                project_path.mkdir(parents=True)

            for item in package_dir.iterdir():
                dest_path = project_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest_path)

            if verbose and not tracker:
                console.print(f"[cyan]Local templates copied to {project_path}[/cyan]")

    except Exception as e:
        error_msg = f"Failed to copy local templates: {e}"
        if tracker:
            tracker.error("local-copy", error_msg)
        raise RuntimeError(error_msg)

    if tracker:
        tracker.complete("local-copy", "templates ready")

    # Copy MCP configuration (local development only)
    copy_mcp_config_local_dev(project_path, ai_assistant, tracker=tracker, verbose=verbose)

    return project_path


def download_and_extract_template(
    project_path: Path,
    ai_assistant: str,
    script_type: str,
    is_current_dir: bool = False,
    *,
    verbose: bool = True,
    tracker: StepTracker | None = None,
    client: httpx.Client = None,
    debug: bool = False,
    github_token: str = None,
    local_dev: bool = False,
) -> Path:
    """Download the latest release and extract it to create a new project.

    If local_dev=True, uses local templates instead of downloading from GitHub.
    Returns project_path. Uses tracker if provided (with keys: fetch, download, extract, cleanup)
    """
    # Route to local development function if requested
    if local_dev:
        return copy_local_template(
            project_path,
            ai_assistant,
            script_type,
            is_current_dir,
            verbose=verbose,
            tracker=tracker,
            debug=debug,
        )

    # Continue with existing GitHub download logic
    current_dir = Path.cwd()

    if tracker:
        tracker.start("fetch", "contacting GitHub API")
    try:
        zip_path, meta = download_template_from_github(
            ai_assistant,
            current_dir,
            script_type=script_type,
            verbose=verbose and tracker is None,
            show_progress=(tracker is None),
            client=client,
            debug=debug,
            github_token=github_token,
        )
        if tracker:
            tracker.complete("fetch", f"release {meta['release']} ({meta['size']:,} bytes)")
            tracker.add("download", "Download template")
            tracker.complete("download", meta["filename"])
    except Exception as e:
        if tracker:
            tracker.error("fetch", str(e))
        else:
            if verbose:
                console.print(f"[red]Error downloading template:[/red] {e}")

        # Always show detailed error in debug mode
        if debug:
            console.print(f"[red]Download/extract error details: {e}[/red]")
            import traceback

            console.print(f"[red]Traceback:[/red] {traceback.format_exc()}")

        raise

    if tracker:
        tracker.add("extract", "Extract template")
        tracker.start("extract")
    elif verbose:
        console.print("Extracting template...")

    try:
        if not is_current_dir:
            project_path.mkdir(parents=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_contents = zip_ref.namelist()
            if tracker:
                tracker.start("zip-list")
                tracker.complete("zip-list", f"{len(zip_contents)} entries")
            elif verbose:
                console.print(f"[cyan]ZIP contains {len(zip_contents)} items[/cyan]")

            if is_current_dir:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    zip_ref.extractall(temp_path)

                    extracted_items = list(temp_path.iterdir())
                    if tracker:
                        tracker.start("extracted-summary")
                        tracker.complete("extracted-summary", f"temp {len(extracted_items)} items")
                    elif verbose:
                        console.print(f"[cyan]Extracted {len(extracted_items)} items to temp location[/cyan]")

                    source_dir = temp_path
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        source_dir = extracted_items[0]
                        if tracker:
                            tracker.add("flatten", "Flatten nested directory")
                            tracker.complete("flatten")
                        elif verbose:
                            console.print("[cyan]Found nested directory structure[/cyan]")

                    for item in source_dir.iterdir():
                        dest_path = project_path / item.name
                        if item.is_dir():
                            if dest_path.exists():
                                if verbose and not tracker:
                                    console.print(f"[yellow]Merging directory:[/yellow] {item.name}")
                                for sub_item in item.rglob("*"):
                                    if sub_item.is_file():
                                        rel_path = sub_item.relative_to(item)
                                        dest_file = dest_path / rel_path
                                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                                        shutil.copy2(sub_item, dest_file)
                            else:
                                shutil.copytree(item, dest_path)
                        else:
                            if dest_path.exists() and verbose and not tracker:
                                console.print(f"[yellow]Overwriting file:[/yellow] {item.name}")
                            shutil.copy2(item, dest_path)
                    if verbose and not tracker:
                        console.print("[cyan]Template files merged into current directory[/cyan]")
            else:
                zip_ref.extractall(project_path)

                extracted_items = list(project_path.iterdir())
                if tracker:
                    tracker.start("extracted-summary")
                    tracker.complete("extracted-summary", f"{len(extracted_items)} top-level items")
                elif verbose:
                    console.print(f"[cyan]Extracted {len(extracted_items)} items to {project_path}:[/cyan]")
                    for item in extracted_items:
                        console.print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")

                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    nested_dir = extracted_items[0]
                    temp_move_dir = project_path.parent / f"{project_path.name}_temp"

                    shutil.move(str(nested_dir), str(temp_move_dir))

                    project_path.rmdir()

                    shutil.move(str(temp_move_dir), str(project_path))
                    if tracker:
                        tracker.add("flatten", "Flatten nested directory")
                        tracker.complete("flatten")
                    elif verbose:
                        console.print(f"[cyan]Flattened nested directory structure[/cyan]")

    except Exception as e:
        if tracker:
            tracker.error("extract", str(e))
        else:
            if verbose:
                console.print(f"[red]Error extracting template:[/red] {e}")
                if debug:
                    console.print(Panel(str(e), title="Extraction Error", border_style="red"))

        if not is_current_dir and project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(1)
    else:
        if tracker:
            tracker.complete("extract")
    finally:
        if tracker:
            tracker.add("cleanup", "Remove temporary archive")

        if zip_path.exists():
            zip_path.unlink()
            if tracker:
                tracker.complete("cleanup")
            elif verbose:
                console.print(f"Cleaned up: {zip_path.name}")

    return project_path


def copy_mcp_config_local_dev(
    project_path: Path, ai_assistant: str, tracker: StepTracker | None = None, verbose: bool = True
) -> None:
    """Copy MCP configuration file to the assistant-specific location (local development only)."""
    # Get repo root directory (where this CLI script is located)
    repo_root = Path(__file__).parent.parent.parent
    mcp_source = repo_root / "mcps" / "mcp.json"

    if not mcp_source.exists():
        if tracker:
            tracker.skip("mcp-config", "no MCP config found")
        elif verbose:
            console.print("[yellow]No MCP configuration found, skipping[/yellow]")
        return

    # Determine destination path based on AI assistant
    if ai_assistant == "claude":
        mcp_dest = project_path / ".mcp.json"
        location_desc = ".mcp.json (Claude Code)"
    elif ai_assistant == "kilocode":
        mcp_dest = project_path / ".kilocode" / "mcp.json"
        location_desc = ".kilocode/mcp.json (Kilo Code)"
    elif ai_assistant == "q":
        mcp_dest = project_path / ".amazonq" / "mcp.json"
        location_desc = ".amazonq/mcp.json (Amazon Q)"
    else:
        if tracker:
            tracker.skip("mcp-config", f"unsupported assistant: {ai_assistant}")
        elif verbose:
            console.print(f"[yellow]MCP config not supported for {ai_assistant}, skipping[/yellow]")
        return

    try:
        if tracker:
            tracker.add("mcp-config", "Copy MCP configuration")
            tracker.start("mcp-config")
        elif verbose:
            console.print("[cyan]Copying MCP configuration...[/cyan]")

        # Create parent directory if needed
        mcp_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mcp_source, mcp_dest)

        if tracker:
            tracker.complete("mcp-config", location_desc)
        elif verbose:
            console.print(f"[green]✓[/green] MCP configuration copied to {location_desc}")

    except Exception as e:
        error_msg = f"Failed to copy MCP config: {e}"
        if tracker:
            tracker.error("mcp-config", error_msg)
        elif verbose:
            console.print(f"[red]Error copying MCP config:[/red] {e}")


def ensure_executable_scripts(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Ensure POSIX .sh scripts under .specify/scripts (recursively) have execute bits (no-op on Windows)."""
    if os.name == "nt":
        return  # Windows: skip silently
    scripts_root = project_path / ".evalkit" / "scripts"
    if not scripts_root.is_dir():
        return
    failures: list[str] = []
    updated = 0
    for script in scripts_root.rglob("*.sh"):
        try:
            if script.is_symlink() or not script.is_file():
                continue
            try:
                with script.open("rb") as f:
                    if f.read(2) != b"#!":
                        continue
            except Exception:
                continue
            st = script.stat()
            mode = st.st_mode
            if mode & 0o111:
                continue
            new_mode = mode
            if mode & 0o400:
                new_mode |= 0o100
            if mode & 0o040:
                new_mode |= 0o010
            if mode & 0o004:
                new_mode |= 0o001
            if not (new_mode & 0o100):
                new_mode |= 0o100
            os.chmod(script, new_mode)
            updated += 1
        except Exception as e:
            failures.append(f"{script.relative_to(scripts_root)}: {e}")
    if tracker:
        detail = f"{updated} updated" + (f", {len(failures)} failed" if failures else "")
        tracker.add("chmod", "Set script permissions recursively")
        (tracker.error if failures else tracker.complete)("chmod", detail)
    else:
        if updated:
            console.print(f"[cyan]Updated execute permissions on {updated} script(s) recursively[/cyan]")
        if failures:
            console.print("[yellow]Some scripts could not be updated:[/yellow]")
            for f in failures:
                console.print(f"  - {f}")


@app.command()
def init(
    project_name: str = typer.Argument(
        None, help="Name for your new project directory (optional if using --here, or use '.' for current directory)"
    ),
    ai_assistant: str = typer.Option(
        None,
        "--ai",
        help="AI assistant to use: kilocode, claude, or q",
    ),
    script_type: str = typer.Option(None, "--script", help="Script type to use: sh or ps"),
    ignore_agent_tools: bool = typer.Option(
        False, "--ignore-agent-tools", help="Skip checks for AI agent tools like Claude Code"
    ),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git repository initialization"),
    here: bool = typer.Option(
        False, "--here", help="Initialize project in the current directory instead of creating a new one"
    ),
    force: bool = typer.Option(False, "--force", help="Force merge/overwrite when using --here (skip confirmation)"),
    skip_tls: bool = typer.Option(False, "--skip-tls", help="Skip SSL/TLS verification (not recommended)"),
    debug: bool = typer.Option(
        False, "--debug", help="Show verbose diagnostic output for network and extraction failures"
    ),
    github_token: str = typer.Option(
        None,
        "--github-token",
        help="GitHub token to use for API requests (or set GH_TOKEN or GITHUB_TOKEN environment variable)",
    ),
    local_dev: bool = typer.Option(
        False, "--local-dev", help="Use local templates instead of downloading from GitHub (for development)"
    ),
):
    """
    Initialize a new EvalKit project from the latest template.

    This command will:
    1. Check that required tools are installed (git is optional)
    2. Let you choose your AI assistant
    3. Download the appropriate template from GitHub (or use local templates with --local-dev)
    4. Extract the template to a new project directory or current directory
    5. Initialize a fresh git repository (if not --no-git and no existing repo)
    6. Optionally set up AI assistant commands

    Examples:
        evalkit init my-project
        evalkit init my-project --ai claude
        evalkit init my-project --ai kilocode --no-git
        evalkit init --ignore-agent-tools my-project
        evalkit init . --ai claude         # Initialize in current directory
        evalkit init .                     # Initialize in current directory (interactive AI selection)
        evalkit init --here --ai claude    # Alternative syntax for current directory
        evalkit init --here --ai q
        evalkit init --here --ai kilocode
        evalkit init --here
        evalkit init --here --force        # Skip confirmation when current directory not empty

    Development Examples:
        evalkit init demo-project --local-dev --ai kilocode    # Use local templates for development
        evalkit init --here --local-dev --ai claude           # Use local templates in current directory
    """

    show_banner()

    if project_name == ".":
        here = True
        project_name = None  # Clear project_name to use existing validation logic

    if here and project_name:
        console.print("[red]Error:[/red] Cannot specify both project name and --here flag")
        raise typer.Exit(1)

    if not here and not project_name:
        console.print(
            "[red]Error:[/red] Must specify either a project name, use '.' for current directory, or use --here flag"
        )
        raise typer.Exit(1)

    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()

        existing_items = list(project_path.iterdir())
        if existing_items:
            console.print(f"[yellow]Warning:[/yellow] Current directory is not empty ({len(existing_items)} items)")
            console.print(
                "[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]"
            )
            if force:
                console.print("[cyan]--force supplied: skipping confirmation and proceeding with merge[/cyan]")
            else:
                response = typer.confirm("Do you want to continue?")
                if not response:
                    console.print("[yellow]Operation cancelled[/yellow]")
                    raise typer.Exit(0)
    else:
        project_path = Path(project_name).resolve()
        if project_path.exists():
            if local_dev:
                # Allow re-initialization for local development
                console.print(f"[yellow]Warning:[/yellow] Directory '[cyan]{project_name}[/cyan]' already exists")
                console.print("[yellow]Local development mode: will overwrite existing templates and scripts[/yellow]")
            else:
                error_panel = Panel(
                    f"Directory '[cyan]{project_name}[/cyan]' already exists\n"
                    "Please choose a different project name or remove the existing directory.\n\n"
                    "Tip: Use [cyan]--local-dev[/cyan] to allow re-initialization for development",
                    title="[red]Directory Conflict[/red]",
                    border_style="red",
                    padding=(1, 2),
                )
                console.print()
                console.print(error_panel)
                raise typer.Exit(1)

    current_dir = Path.cwd()

    setup_lines = [
        "[cyan]EvalKit Project Setup[/cyan]",
        "",
        f"{'Project':<15} [green]{project_path.name}[/green]",
        f"{'Working Path':<15} [dim]{current_dir}[/dim]",
    ]

    if not here:
        setup_lines.append(f"{'Target Path':<15} [dim]{project_path}[/dim]")

    console.print(Panel("\n".join(setup_lines), border_style="cyan", padding=(1, 2)))

    should_init_git = False
    if not no_git:
        should_init_git = check_tool("git")
        if not should_init_git:
            console.print("[yellow]Git not found - will skip repository initialization[/yellow]")

    if ai_assistant:
        if ai_assistant not in AGENT_CONFIG:
            console.print(
                f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(AGENT_CONFIG.keys())}"
            )
            raise typer.Exit(1)
        selected_ai = ai_assistant
    else:
        # Create options dict for selection (agent_key: display_name)
        ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
        selected_ai = select_with_arrows(ai_choices, "Choose your AI assistant", "claude")

    if not ignore_agent_tools:
        agent_config = AGENT_CONFIG.get(selected_ai)
        if agent_config and agent_config["requires_cli"]:
            install_url = agent_config["install_url"]
            if not check_tool(selected_ai):
                error_panel = Panel(
                    f"[cyan]{selected_ai}[/cyan] not found\n"
                    f"Install from: [cyan]{install_url}[/cyan]\n"
                    f"{agent_config['name']} is required to continue with this project type.\n\n"
                    "Tip: Use [cyan]--ignore-agent-tools[/cyan] to skip this check",
                    title="[red]Agent Detection Error[/red]",
                    border_style="red",
                    padding=(1, 2),
                )
                console.print()
                console.print(error_panel)
                raise typer.Exit(1)

    if script_type:
        if script_type not in SCRIPT_TYPE_CHOICES:
            console.print(
                f"[red]Error:[/red] Invalid script type '{script_type}'. Choose from: {', '.join(SCRIPT_TYPE_CHOICES.keys())}"
            )
            raise typer.Exit(1)
        selected_script = script_type
    else:
        default_script = "ps" if os.name == "nt" else "sh"

        if sys.stdin.isatty():
            selected_script = select_with_arrows(SCRIPT_TYPE_CHOICES, "Choose script type", default_script)
        else:
            selected_script = default_script

    console.print(f"[cyan]Selected AI assistant:[/cyan] {selected_ai}")
    console.print(f"[cyan]Selected script type:[/cyan] {selected_script}")

    tracker = StepTracker("Initialize EvalKit Project")

    sys._specify_tracker_active = True

    tracker.add("precheck", "Check required tools")
    tracker.complete("precheck", "ok")
    tracker.add("ai-select", "Select AI assistant")
    tracker.complete("ai-select", f"{selected_ai}")
    tracker.add("script-select", "Select script type")
    tracker.complete("script-select", selected_script)

    # Add tracker steps based on whether we're using local development or GitHub download
    if local_dev:
        for key, label in [
            ("local-build", "Build local templates"),
            ("local-copy", "Copy processed templates"),
            ("chmod", "Ensure scripts executable"),
            ("mcp-config", "Copy MCP configuration"),
            ("git", "Initialize git repository"),
            ("final", "Finalize"),
        ]:
            tracker.add(key, label)
    else:
        for key, label in [
            ("fetch", "Fetch latest release"),
            ("download", "Download template"),
            ("extract", "Extract template"),
            ("zip-list", "Archive contents"),
            ("extracted-summary", "Extraction summary"),
            ("chmod", "Ensure scripts executable"),
            ("cleanup", "Cleanup"),
            ("git", "Initialize git repository"),
            ("final", "Finalize"),
        ]:
            tracker.add(key, label)

    # Track git error message outside Live context so it persists
    git_error_message = None

    with Live(tracker.render(), console=console, refresh_per_second=8, transient=True) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        try:
            verify = not skip_tls
            local_ssl_context = ssl_context if verify else False
            local_client = httpx.Client(verify=local_ssl_context)

            download_and_extract_template(
                project_path,
                selected_ai,
                selected_script,
                here,
                verbose=False,
                tracker=tracker,
                client=local_client,
                debug=debug,
                github_token=github_token,
                local_dev=local_dev,
            )

            ensure_executable_scripts(project_path, tracker=tracker)

            if not no_git:
                tracker.start("git")
                if is_git_repo(project_path):
                    tracker.complete("git", "existing repo detected")
                elif should_init_git:
                    success, error_msg = init_git_repo(project_path, quiet=True)
                    if success:
                        tracker.complete("git", "initialized")
                    else:
                        tracker.error("git", "init failed")
                        git_error_message = error_msg
                else:
                    tracker.skip("git", "git not available")
            else:
                tracker.skip("git", "--no-git flag")

            tracker.complete("final", "project ready")
        except Exception as e:
            tracker.error("final", str(e))
            if debug:
                console.print(f"[red]Final exception details: {e}[/red]")
                console.print(f"[red]Exception type: {type(e)}[/red]")
                import traceback

                console.print(f"[red]Traceback:[/red] {traceback.format_exc()}")
            console.print(Panel(f"Initialization failed: {e}", title="Failure", border_style="red"))
            if debug:
                _env_pairs = [
                    ("Python", sys.version.split()[0]),
                    ("Platform", sys.platform),
                    ("CWD", str(Path.cwd())),
                ]
                _label_width = max(len(k) for k, _ in _env_pairs)
                env_lines = [f"{k.ljust(_label_width)} → [bright_black]{v}[/bright_black]" for k, v in _env_pairs]
                console.print(Panel("\n".join(env_lines), title="Debug Environment", border_style="magenta"))
            if not here and project_path.exists():
                shutil.rmtree(project_path)
            raise typer.Exit(1)
        finally:
            pass

    console.print(tracker.render())
    console.print("\n[bold green]Project ready.[/bold green]")

    # Show git error details if initialization failed
    if git_error_message:
        console.print()
        git_error_panel = Panel(
            f"[yellow]Warning:[/yellow] Git repository initialization failed\n\n"
            f"{git_error_message}\n\n"
            f"[dim]You can initialize git manually later with:[/dim]\n"
            f"[cyan]cd {project_path if not here else '.'}[/cyan]\n"
            f"[cyan]git init[/cyan]\n"
            f"[cyan]git add .[/cyan]\n"
            f'[cyan]git commit -m "Initial commit"[/cyan]',
            title="[red]Git Initialization Failed[/red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(git_error_panel)

    # Agent folder security notice
    agent_config = AGENT_CONFIG.get(selected_ai)
    if agent_config:
        agent_folder = agent_config["folder"]
        security_notice = Panel(
            f"Some agents may store credentials, auth tokens, or other identifying and private artifacts in the agent folder within your project.\n"
            f"Consider adding [cyan]{agent_folder}[/cyan] (or parts of it) to [cyan].gitignore[/cyan] to prevent accidental credential leakage.",
            title="[yellow]Agent Folder Security[/yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
        console.print()
        console.print(security_notice)

    steps_lines = []
    if not here:
        steps_lines.append(f"1. Go to the project folder: [cyan]cd {project_name}[/cyan]")
        step_num = 2
    else:
        steps_lines.append("1. You're already in the project directory!")
        step_num = 2

    # Add Codex-specific setup step if needed
    if selected_ai == "codex":
        codex_path = project_path / ".codex"
        quoted_path = shlex.quote(str(codex_path))
        if os.name == "nt":  # Windows
            cmd = f"setx CODEX_HOME {quoted_path}"
        else:  # Unix-like systems
            cmd = f"export CODEX_HOME={quoted_path}"

        steps_lines.append(
            f"{step_num}. Set [cyan]CODEX_HOME[/cyan] environment variable before running Codex: [cyan]{cmd}[/cyan]"
        )
        step_num += 1

    # Add AI agent startup instruction
    agent_config = AGENT_CONFIG.get(selected_ai)
    if agent_config:
        if selected_ai == "claude":
            steps_lines.append(f"{step_num}. Start Claude Code by running: [cyan]claude[/cyan]")
        elif selected_ai == "kilocode":
            steps_lines.append(f"{step_num}. Open your IDE with Kilo Code extension enabled")
        elif selected_ai == "q":
            steps_lines.append(f"{step_num}. Start Amazon Q Developer CLI by running: [cyan]q[/cyan]")
        else:
            steps_lines.append(f"{step_num}. Start your AI agent: [cyan]{selected_ai}[/cyan]")
        step_num += 1

    steps_lines.append(f"{step_num}. Start using slash commands with your AI agent:")

    steps_lines.append(f"   {step_num}.1 [cyan]/evalkit.plan[/] - Analyze your agent and design evaluation strategy")
    steps_lines.append(f"   {step_num}.2 [cyan]/evalkit.data[/] - Generate test cases for evaluation")
    steps_lines.append(f"   {step_num}.3 [cyan]/evalkit.trace[/] - Set up tracing")
    steps_lines.append(f"   {step_num}.4 [cyan]/evalkit.run_agent[/] - Run agent tests and collect traces")
    steps_lines.append(
        f"   {step_num}.5 [cyan]/evalkit.eval[/] - Evaluate agent test results with the generated traces"
    )
    steps_lines.append(
        f"   {step_num}.6 [cyan]/evalkit.report[/] - Analyze results and provide improvement recommendations"
    )
    steps_lines.append("")
    steps_lines.append("   [dim]Or run the complete pipeline automatically:[/dim]")
    steps_lines.append("   [cyan]/evalkit.auto[/] - Run all commands above sequentially with auto-approval")

    steps_panel = Panel("\n".join(steps_lines), title="Next Steps", border_style="cyan", padding=(1, 2))
    console.print()
    console.print(steps_panel)

    # enhancement_lines = [
    #     "Optional command that you can use for your evaluation [bright_black](improve evaluation quality)[/bright_black]",
    #     "",
    #     "○ [cyan]/evalkit.clarify[/] [bright_black](optional)[/bright_black] - Clarify underspecified areas in evaluation design (run before [cyan]/evalkit.plan[/] if used)",
    # ]
    # enhancements_panel = Panel(
    #     "\n".join(enhancement_lines), title="Enhancement Commands", border_style="cyan", padding=(1, 2)
    # )
    # console.print()
    # console.print(enhancements_panel)


@app.command()
def check():
    """Check that all required tools are installed."""
    show_banner()
    console.print("[bold]Checking for installed tools...[/bold]\n")

    tracker = StepTracker("Check Available Tools")

    tracker.add("git", "Git version control")
    git_ok = check_tool("git", tracker=tracker)

    agent_results = {}
    for agent_key, agent_config in AGENT_CONFIG.items():
        agent_name = agent_config["name"]

        tracker.add(agent_key, agent_name)
        agent_results[agent_key] = check_tool(agent_key, tracker=tracker)

    # Check VS Code variants (not in agent config)
    tracker.add("code", "Visual Studio Code")
    code_ok = check_tool("code", tracker=tracker)

    tracker.add("code-insiders", "Visual Studio Code Insiders")
    code_insiders_ok = check_tool("code-insiders", tracker=tracker)

    console.print(tracker.render())

    console.print("\n[bold green]EvalKit is ready to use![/bold green]")

    if not git_ok:
        console.print("[dim]Tip: Install git for repository management[/dim]")

    if not any(agent_results.values()):
        console.print("[dim]Tip: Install an AI assistant for the best experience[/dim]")


def main():
    app()


if __name__ == "__main__":
    main()
