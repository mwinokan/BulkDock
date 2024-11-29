import mrich
import logging
from pathlib import Path

mrich.debug("from fragmenstein import Wictor, Laboratory")
from fragmenstein import Wictor, Laboratory  # , Igor

mrich.debug("from fragmenstein.laboratory.validator import place_input_validator")
from fragmenstein.laboratory.validator import place_input_validator

from pandas import DataFrame
from .io import mols_to_sdf


def fragmenstein_place(
    *,
    animal: "HIPPO",
    scratch_dir: "Path",
    compound: "Compound",
    reference: "Pose",
    inspirations: "PoseSet",
    protein_path: "Path",
    # ref_hits_path: "Path",
    n_cores: int = 8,
    n_retries: int = 3,
    timeout: int = 300,
    write_hit_mols: bool = True,
    metadata: dict | None = None,
) -> "Pose | bool":

    metadata = metadata or {}

    # set up lab
    laboratory = setup_wictor_laboratory(
        scratch_dir=scratch_dir, protein_path=protein_path
    )

    # create inputs
    queries = create_fragmenstein_queries_df(
        compound=compound, reference=reference, inspirations=inspirations
    )

    # validate inputs
    queries = place_input_validator(queries)

    name = queries.at[0, "name"]
    smiles = queries.at[0, "smiles"]
    subdir = scratch_dir / name

    mrich.h3("Fragmenstein info")
    mrich.var("name", name)
    mrich.var("smiles", smiles)
    mrich.var("scratch_dir", scratch_dir)
    mrich.var("subdir", subdir)
    mrich.var("protein_path", protein_path)

    for attempt in range(n_retries):

        # run the placement
        result = laboratory.place(
            queries,
            n_cores=n_cores,
            timeout=timeout,
        )

        # process outputs

        if result is None:
            mrich.error("Placement null result")
            continue

        assert len(result) == 1

        result = result.iloc[0].to_dict()

        if result["outcome"] == "crashed" and result["error"] == "TimeoutError":
            mrich.error("Placement timed out")
            continue

        mrich.h3("Placement Result")

        mrich.var("name", result["name"])
        mrich.var("error", result["error"])
        mrich.var("mode", result["mode"])
        mrich.var("∆∆G", result["∆∆G"])
        mrich.var("comRMSD", result["comRMSD"])
        mrich.var("runtime", result["runtime"])
        mrich.var("outcome", result["outcome"])

        # write some mols to files for debugging
        if write_hit_mols:
            mols_to_sdf(result["hit_mols"], subdir / "hit_mols.sdf")

        break

    ## into HIPPO database

    mol_path = subdir / f"{name}.minimised.mol"

    if mol_path.exists():
        metadata["scratch_subdir"] = str(subdir.resolve()),
        metadata["fragmenstein_runtime"] = result["runtime"],
        metadata["fragmenstein_outcome"] = result["outcome"],
        metadata["fragmenstein_mode"] = result["mode"],
        metadata["fragmenstein_error"] = result["error"],

        pose_id = animal.register_pose(
            compound=compound,
            target=1,
            path=mol_path,
            reference=reference,
            inspirations=inspirations,
            tags=["Fragmenstein placed"],
            energy_score=result["∆∆G"],
            distance_score=result["comRMSD"],
            metadata=metadata,
            commit=True,
            return_pose=False,
        )

        mrich.success(f"Registered Pose {pose_id}")

        return pose_id

    else:

        mrich.error("Placement not successful")

        return False


# from syndirella.slipper.SlipperFitter.setup_Fragmenstein
def setup_wictor_laboratory(
    *,
    scratch_dir: "Path",
    protein_path: "Path",
    monster_joining_cutoff: float = 5,  # Å
) -> "Laboratory":

    # from fragmenstein import Laboratory, Wictor, Igor
    assert Path(scratch_dir).exists(), f"{scratch_dir=} does not exist"
    assert Path(protein_path).exists(), f"{protein_path=} does not exist"

    # set up Wictor
    Wictor.work_path = scratch_dir
    Wictor.monster_throw_on_discard = True  # stop if fragment unusable
    Wictor.monster_joining_cutoff = monster_joining_cutoff
    Wictor.quick_reanimation = False  # for the impatient
    Wictor.error_to_catch = Exception  # stop the whole laboratory otherwise
    Wictor.enable_stdout(logging.CRITICAL)
    Wictor.enable_logfile(scratch_dir / f"fragmenstein.log", logging.DEBUG)

    # os.chdir(output_path)  # needed?

    Laboratory.Victor = Wictor

    # Igor.init_pyrosetta() # needed?

    with open(protein_path) as fh:
        pdbblock: str = fh.read()

    lab = Laboratory(pdbblock=pdbblock, covalent_resi=None, run_plip=False)

    return lab


def create_fragmenstein_queries_df(
    *, compound: "Compound", reference: "Pose", inspirations: "PoseSet"
):

    return DataFrame(
        [
            {
                "name": f"{compound}-{reference}",
                "smiles": compound.smiles,
                "hits": [pose.mol for pose in inspirations],
            }
        ]
    )
