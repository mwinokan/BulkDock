import mrich
from typer import Typer
from .bulkdock import BulkDock

HELP = """
💪 BulkDock: Manage batches of Fragmenstein restrained protein-ligand docking jobs
"""

app = Typer(help=HELP, no_args_is_help=True)
engine = BulkDock()


@app.command()
def status():
    """Show the status of BulkDock jobs"""
    mrich.title("STATUS GOES HERE")


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
    )


@app.command()
def place(target: str, file: str):
    """Start a placement job.

    Input file must be a CSV with the first column containing the SMILES and all subsequent columns containing observation shortcodes for inspiration hits

    """
    engine.place(target, file)


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
