import mrich
import typer
from .bulkdock import BulkDock

HELP = """
💪 BulkDock: INTERNAL CLI ONLY!
"""

app = typer.Typer()
engine = BulkDock()

"""Inner CLI for batch jobs"""


@app.command()
def place(target: str, file: str):
    mrich.var("target", target)
    mrich.var("file", file)
    engine.place(target, file)


def main():
    app()


if __name__ == "__main__":
    main()
