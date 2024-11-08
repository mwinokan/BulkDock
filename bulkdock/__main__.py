import mrich
import typer
from .bulkdock import BulkDock
from typing import Optional
from typing_extensions import Annotated

HELP = """
💪 BulkDock: Manage batches of Fragmenstein restrained protein-ligand docking jobs
"""

app = typer.Typer(help=HELP, no_args_is_help=True)
engine = BulkDock()


def human_timedelta_to_seconds(s):

    values = s.split()

    seconds = 0

    for value in values:
        if value.endswith("s"):
            seconds += int(value[:-1])
        elif value.endswith("m"):
            seconds += 60 * int(value[:-1])
        elif value.endswith("h"):
            seconds += 60 * 60 * int(value[:-1])
        elif value.endswith("d"):
            seconds += 24 * 60 * 60 * int(value[:-1])

    return seconds


@app.command()
def status():
    """Show the status of running BulkDock jobs"""

    import subprocess
    from rich.table import Table
    from rich.panel import Panel
    from richqueue.slurm import combined_df
    from richqueue.table import color_by_state, COLUMNS
    from datetime import timedelta
    from richqueue.tools import human_timedelta  # , human_timedelta_to_seconds

    df = combined_df()

    # filter dataframe
    df = df[df["name"].str.startswith("BulkDock")]
    df = df[df["job_state"].isin(["RUNNING", "PENDING"])]
    df = df[["name", "job_id", "run_time", "standard_output", "job_state"]]

    # create the table
    table = Table(title="Active BulkDock Jobs", box=None, header_style="")

    table.add_column(**COLUMNS["job_id"])
    table.add_column("[cyan3 underline]Command", style="cyan3")
    table.add_column("[cyan3 underline]Target", style="cyan3")
    table.add_column(**COLUMNS["name"])
    table.add_column(**COLUMNS["run_time"])
    table.add_column(**COLUMNS["job_state"])
    table.add_column(
        "[cornflower_blue underline]Attempted", justify="right", style="cornflower_blue"
    )
    table.add_column(
        "[bold underline]Progress", justify="right", style="bold cornflower_blue"
    )
    table.add_column(
        "[bold underline]Performance", justify="right", style="bold cornflower_blue"
    )
    table.add_column(
        "[cornflower_blue underline]Remaining", justify="right", style="cornflower_blue"
    )

    def color_by_fraction(fraction):

        if fraction > 0.75:
            color = "bright_green"
        elif fraction > 0.50:
            color = "bright_yellow"
        elif fraction > 0.25:
            color = "dark_orange"
        else:
            color = "red"

        return f"[{color}]{fraction*100:.1f} %"

    def color_by_performance(performance):

        if performance < 10:
            color = "bright_green"
        elif performance < 20:
            color = "bright_yellow"
        elif performance < 60:
            color = "dark_orange"
        else:
            color = "red"

        return f"[{color}]{performance:.2f} s/it"

    for i, row in df.iterrows():

        values = []

        name = row["name"]

        command, target, name = name.split(":")
        command = command.removeprefix("BulkDock.")

        # calculate placement progress

        grep = [f'grep "Placement task " {row.standard_output} | tail -n 1']

        x = subprocess.Popen(
            grep, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        output = x.communicate()

        progress = output[0].decode()

        if len(progress) < 15:
            progress = ""

        else:
            i, n = progress.split("Placement task ")[-1].split(" ")[0].split("/")

            i = int(i)
            n = int(n)

            fraction = i / n

            progress = color_by_fraction(fraction)

        # calculate performance

        run_seconds = human_timedelta_to_seconds(row.run_time)

        performance = color_by_performance(run_seconds / i)

        # calculate remaining estimate

        remaining = (n - i) * (run_seconds / i)
        remaining = human_timedelta(timedelta(seconds=remaining))

        values.append(str(row.job_id))
        values.append(command)
        values.append(target)
        values.append(name)
        values.append(str(row.run_time))
        values.append(color_by_state(row.job_state))
        values.append(str(i))
        values.append(progress)
        values.append(performance)
        values.append(str(remaining))

        table.add_row(*values)

    mrich.print(Panel(table, expand=False))


@app.command()
def to_fragalysis(
    target: str,
    sdf_file: str,
    method: str,
    generate_pdbs: bool = False,
    submitter_name: str = None,
    submitter_institution: str = None,
    submitter_email: str = None,
    ref_url: str = None,
    max_energy_score: float | None = 0.0,
    max_distance_score: float | None = 2.0,
    require_outcome: str | None = "acceptable",
    output: str | None = None,
):
    """Export poses from a successful output into a Fragalysis-ready format"""
    engine.to_fragalysis(
        target=target,
        sdf_file=sdf_file,
        method=method,
        generate_pdbs=generate_pdbs,
        submitter_name=submitter_name,
        submitter_institution=submitter_institution,
        submitter_email=submitter_email,
        ref_url=ref_url,
        max_energy_score=max_energy_score,
        max_distance_score=max_distance_score,
        require_outcome=require_outcome,
        output=output,
    )


@app.command()
def place(
    target: str,
    file: str,
    split: int = 6_000,
    stagger: int = 1,
):
    """Start a placement job.

    Input file must be a CSV with the first column containing the SMILES and all subsequent columns containing observation shortcodes for inspiration hits

    """
    # :param target: to place against
    # :param name: or path to input file (must be in configured INPUTS directory)
    # :param split: split the input file into batches of this size

    engine.submit_placement_jobs(target, file, split=split, stagger=stagger)


@app.command()
def configure(variable: str, value: str):
    """Configure"""
    mrich.h2("BulkDock.configure")
    mrich.var("variable", variable)
    mrich.var("value", value)
    from .config import VARIABLES

    assert variable in VARIABLES
    engine.set_config_value(variable, value)


@app.command()
def create_directories():
    """Create directories as configured"""
    engine.create_directories()


@app.command()
def extract(target: str):
    """Extract target zip file"""
    engine.extract_target(target)


@app.command()
def setup(target: str):
    """Setup HIPPO Database for a target"""
    engine.setup_hippo(target)


def main():
    app()


if __name__ == "__main__":
    main()
