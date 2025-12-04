import typer
from rich import print as rprint

from smart_commit.commands.init import init_cmd
from smart_commit.commands.propose import propose_cmd
from smart_commit.commands.push import push_cmd
from smart_commit.commands.integration import integration_app
from smart_commit.commands.plugin import plugin_app

app = typer.Typer(
    name="smart-commit",
    help="🧠 AI-powered commit assistant with task management integration",
    no_args_is_help=True,
    rich_markup_mode="rich"
)

app.command("init")(init_cmd)
app.command("propose")(propose_cmd)
app.command("push")(push_cmd)
app.add_typer(integration_app, name="integration")
app.add_typer(plugin_app, name="plugin")

def main():
    app()

if __name__ == "__main__":
    main()