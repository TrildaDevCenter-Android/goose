import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import click
from rich import print
from ruamel.yaml import YAML

from goose.cli.config import SESSIONS_PATH
from goose.cli.session import Session
from goose.utils import load_plugins
from goose.utils.session_file import list_sorted_session_files


@click.group()
def goose_cli() -> None:
    pass


@goose_cli.command()
def version() -> None:
    """Lists the version of goose and any plugins"""
    from importlib.metadata import entry_points, version

    print(f"[green]Goose-ai[/green]: [bold][cyan]{version('goose-ai')}[/cyan][/bold]")
    print("[green]Plugins[/green]:")
    entry_points = entry_points(group="metadata.plugins")
    modules = set()

    for ep in entry_points:
        module_name = ep.name
        modules.add(module_name)
    modules.remove("goose-ai")
    for module in sorted(list(modules)):
        # TODO: figure out how to get this to work for goose plugins block
        # as the module name is set to block.goose.cli
        # module_name = 'goose-plugins-block'
        try:
            module_version = version(module)
            print(f"  Module: [green]{module}[/green], Version: [bold][cyan]{module_version}[/cyan][/bold]")
        except Exception as e:
            print(f"  [red]Could not retrieve version for {module}: {e}[/red]")


@goose_cli.group()
def session() -> None:
    """Start or manage sessions"""
    pass


@session.command(name="start")
@click.option("--profile")
@click.option("--plan", type=click.Path(exists=True))
def session_start(profile: str, plan: Optional[str] = None) -> None:
    """Start a new goose session"""
    if plan:
        yaml = YAML()
        with open(plan, "r") as f:
            _plan = yaml.load(f)
    else:
        _plan = None

    session = Session(profile=profile, plan=_plan)
    session.run()


@session.command(name="resume")
@click.argument("name", required=False)
@click.option("--profile")
def session_resume(name: Optional[str], profile: str) -> None:
    """Resume an existing goose session"""
    if name is None:
        session_files = get_session_files()
        if session_files:
            name = list(session_files.keys())[0]
            print(f"Resuming most recent session: {name} from {session_files[name]}")
        else:
            print("No sessions found.")
            return
    session = Session(name=name, profile=profile)
    session.run()


@session.command(name="list")
def session_list() -> None:
    """List goose sessions"""
    session_files = get_session_files().items()
    for session_name, session_file in session_files:
        print(f"{datetime.fromtimestamp(session_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}    {session_name}")


@session.command(name="clear")
@click.option("--keep", default=3, help="Keep this many entries, default 3")
def session_clear(keep: int) -> None:
    """Delete old goose sessions, keeping the most recent sessions up to the specified number"""
    for i, (_, session_file) in enumerate(get_session_files().items()):
        if i >= keep:
            session_file.unlink()


def get_session_files() -> Dict[str, Path]:
    return list_sorted_session_files(SESSIONS_PATH)


all_cli_groups = load_plugins("goose.cli.group")
all_cli_group_options = load_plugins("goose.cli.group_option")


@click.group(
    # we only want to override --help if there are top-level command options
    invoke_without_command=len(all_cli_group_options.items()) > 0,
    name="goose",
    help="AI-powered tool to assist in solving programming and operational tasks",
)
@click.pass_context
def cli(_: click.Context, **kwargs: Dict) -> None:
    pass


for group in all_cli_groups.values():
    for command in group.commands.values():
        cli.add_command(command)

for option in all_cli_group_options.values():
    cli = option()(cli)

if __name__ == "__main__":
    cli()
