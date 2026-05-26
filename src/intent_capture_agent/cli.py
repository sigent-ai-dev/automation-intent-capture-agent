"""CLI client for the Intent Capture Agent service."""

import json
import time
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(
    name="intent-capture",
    help="Intent Capture Agent CLI — manage remote capture sessions.",
)

console = Console()

INTENT_DIR = ".intent"
CONFIG_FILE = ".intent/config.json"


def _get_agent_url() -> str | None:
    config_path = Path(CONFIG_FILE)
    if config_path.is_file():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        return config.get("capture_agent_url")
    return None


def _require_agent_url(url: str | None) -> str:
    if url:
        return url
    stored = _get_agent_url()
    if stored:
        return stored
    console.print(
        "[red]Error:[/] No capture agent URL configured.\n"
        "  Run: [bold]intent-capture config --url https://your-agent.example.com[/]"
    )
    raise typer.Exit(code=1)


def _call_api(base_url: str, method: str, path: str, body: dict | None = None) -> dict | None:
    """Call the capture agent REST API."""
    import urllib.error
    import urllib.request

    url = f"{base_url.rstrip('/')}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 204:
                return None
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        console.print(f"[red]Error:[/] API returned {e.code}: {error_body}")
        raise typer.Exit(code=1)
    except urllib.error.URLError as e:
        console.print(f"[red]Error:[/] Cannot reach capture agent: {e.reason}")
        raise typer.Exit(code=1)


@app.command()
def config(
    url: str = typer.Option(..., "--url", help="Capture agent service URL"),
):
    """Configure the capture agent service URL."""
    config_path = Path(CONFIG_FILE)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.is_file():
        existing = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        existing = {}

    existing["capture_agent_url"] = url.rstrip("/")
    config_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    console.print(f"[green]Configured:[/] capture agent URL set to {url}")


@app.command("check-service")
def check_service(
    url: str = typer.Option(None, "--url", help="Override capture agent URL"),
):
    """Check if the capture agent service is reachable."""
    import urllib.error
    import urllib.request

    agent_url = _require_agent_url(url)
    health_url = f"{agent_url}/health"

    try:
        with urllib.request.urlopen(health_url, timeout=5) as resp:
            if resp.status == 200:
                console.print(f"[green]Service reachable:[/] {agent_url}")
                console.print("  Ready for `intent-capture start`")
            else:
                console.print(f"[yellow]Warning:[/] {agent_url} returned status {resp.status}")
    except urllib.error.URLError as e:
        console.print(f"[red]Service unreachable:[/] {agent_url}")
        console.print(f"  Error: {e.reason}")
        console.print(
            "\n  The Intent Capture Agent service is not deployed yet."
            "\n  See: https://github.com/sigent-ai-dev/intent-capture-agent/issues/11"
        )
        raise typer.Exit(code=1)


@app.command()
def start(
    url: str = typer.Option(None, "--url", help="Override capture agent URL"),
    project: str = typer.Option(None, "--project", help="Project name for the session"),
):
    """Start a new capture session and get the join URL."""
    agent_url = _require_agent_url(url)

    project_name = project
    if not project_name:
        state_path = Path(INTENT_DIR) / "state.json"
        if state_path.is_file():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            project_name = state.get("project_name", "unnamed")
        else:
            project_name = Path.cwd().name

    result = _call_api(agent_url, "POST", "/sessions", {"project_name": project_name})

    console.print("\n[bold green]Session created[/]")
    console.print(f"  [bold]Session ID:[/]  {result['session_id']}")
    console.print(f"  [bold]Join URL:[/]    {result['join_url']}")
    console.print(f"  [bold]Status:[/]      {result['status']}")
    console.print("\n  Share the join URL with stakeholders.")
    console.print(
        f"  Run [bold]intent-capture connect {result['session_id']}[/] to wait for results."
    )


@app.command()
def status(
    session_id: str = typer.Argument(None, help="Session ID (omit for all active sessions)"),
    url: str = typer.Option(None, "--url", help="Override capture agent URL"),
):
    """Show capture session status."""
    agent_url = _require_agent_url(url)

    if session_id:
        result = _call_api(agent_url, "GET", f"/sessions/{session_id}")
        console.print(f"\n[bold]Session:[/] {session_id}")
        console.print(f"  Status: {result['status']}")
        if result.get("progress"):
            console.print(f"  Sections covered: {result['progress'].get('sections_covered', [])}")
        if result.get("participants"):
            console.print(f"  Participants: {', '.join(result['participants'])}")
    else:
        result = _call_api(agent_url, "GET", "/sessions")
        sessions = result.get("sessions", [])
        if not sessions:
            console.print("[dim]No active sessions[/]")
            return
        for s in sessions:
            status_icon = {"active": "[green]●[/]", "pending": "[yellow]○[/]"}.get(
                s["status"], "[dim]○[/]"
            )
            console.print(
                f"  {status_icon} {s['session_id']}  {s['status']}  "
                f"{s.get('project_name', '')}"
            )


@app.command()
def connect(
    session_id: str = typer.Argument(..., help="Session ID to connect to"),
    url: str = typer.Option(None, "--url", help="Override capture agent URL"),
    poll_interval: int = typer.Option(5, "--poll", help="Seconds between status checks"),
):
    """Wait for a capture session to complete and write results to .intent/."""
    agent_url = _require_agent_url(url)

    console.print(f"[bold]Connecting to session:[/] {session_id}")
    console.print(f"[dim]Polling every {poll_interval}s... press Ctrl+C to detach[/]\n")

    try:
        while True:
            result = _call_api(agent_url, "GET", f"/sessions/{session_id}")
            session_status = result["status"]

            if session_status == "complete":
                console.print("[green bold]Session complete![/]\n")
                break
            elif session_status == "failed":
                console.print(f"[red bold]Session failed:[/] {result.get('error', 'unknown')}")
                raise typer.Exit(code=1)

            progress = result.get("progress", {})
            sections = progress.get("sections_covered", [])
            console.print(
                f"  [dim]{session_status}[/] — sections: {len(sections)}/7 {sections}",
                end="\r",
            )
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]Detached.[/] Session continues in background.")
        console.print(f"  Reconnect: [bold]intent-capture connect {session_id}[/]")
        return

    # Fetch and write result
    intent_result = _call_api(agent_url, "GET", f"/sessions/{session_id}/result")

    intent_path = Path(INTENT_DIR)
    intent_path.mkdir(parents=True, exist_ok=True)
    (intent_path / "adr" / "draft").mkdir(parents=True, exist_ok=True)
    (intent_path / "adr" / "accepted").mkdir(parents=True, exist_ok=True)
    (intent_path / "backlog").mkdir(parents=True, exist_ok=True)

    (intent_path / "intent.md").write_text(intent_result["intent_md"], encoding="utf-8")
    (intent_path / "state.json").write_text(
        json.dumps(intent_result["state"], indent=2) + "\n", encoding="utf-8"
    )
    (intent_path / "audit.md").write_text(intent_result["audit_md"], encoding="utf-8")

    console.print("[bold]Written:[/]")
    console.print(f"  {INTENT_DIR}/intent.md")
    console.print(f"  {INTENT_DIR}/state.json")
    console.print(f"  {INTENT_DIR}/audit.md")
    console.print("\n[bold]Next steps:[/]")
    console.print("  1. Run [bold]intent check[/] to validate")
    console.print("  2. Run [bold]/intent.steer[/] to begin architectural steering")


def main():
    app()
