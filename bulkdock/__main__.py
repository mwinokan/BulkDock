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


@app.command()
def status():
    """Show the status of running BulkDock jobs"""

    from .status import status

    status()


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
