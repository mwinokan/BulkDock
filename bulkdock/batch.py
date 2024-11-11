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


@app.command()
def collate(outname: str, target: str, json_path: str, tag: str = "Fragmenstein"):

    import json
    from pathlib import Path

    mrich.var("outname", outname)
    mrich.var("target", target)
    mrich.var("json_path", json_path)
    mrich.var("tag", tag)

    animal = engine.get_animal(target)

    subdir = engine.get_scratch_subdir(f"{target}_inputs")

    json_path = subdir / Path(json_path).name

    assert json_path.exists(), "JSON Input does not exist"

    job_ids = json.load(open(json_path, "rt"))
    job_ids = set(job_ids)

    assert job_ids, "Null Job IDs"

    mrich.var("job_ids", job_ids)

    pose_ids = set()
    for pose in mrich.track(animal.poses(tag=tag), prefix="Getting poses"):

        job_id = int(Path(pose.path).parent.parent.name)

        if job_id not in job_ids:
            continue

        pose_ids.add(pose.id)

    poses = animal.poses[pose_ids]

    mrich.var("#poses", len(poses))

    outfile = engine.get_outfile_path(outname)
    poses.write_sdf(outfile, name_col="id")

    return outfile


def main():
    app()


if __name__ == "__main__":
    main()
