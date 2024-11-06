from fragmenstein import Wictor, Laboratory, Igor


def fragmenstein_place(
    *,
    scratch_dir: "Path",
    smiles: str,
    protein_path: "Path",
    ref_hits_path: "Path",
) -> None:

    # set up lab
    laboratory = setup_wictor_laboratory(
        scratch_dir=scratch_dir, protein_path=protein_path
    )

    # validate inputs

    # run the placement

    # process outputs

    ## into HIPPO database

    ## into output directory

    # clean up scratch directory

    raise NotImplementedError


# from syndirella.slipper.SlipperFitter.setup_Fragmenstein
def setup_wictor_laboratory(
    *,
    scratch_dir: "Path",
    protein_path: "Path",
    monster_joining_cutoff: float = 5,  # Å
) -> "Laboratory":

    # from fragmenstein import Laboratory, Wictor, Igor
    assert scratch_dir.exists(), f"{scratch_dir=} does not exist"
    assert protein_path.exists(), f"{protein_path=} does not exist"

    # set up Wictor
    Wictor.work_path = scratch_dir
    Wictor.monster_throw_on_discard = True  # stop if fragment unusable
    Wictor.monster_joining_cutoff = monster_joining_cutoff
    Wictor.quick_reanimation = False  # for the impatient
    Wictor.error_to_catch = Exception  # stop the whole laboratory otherwise
    Wictor.enable_stdout(logging.CRITICAL)
    Wictor.enable_logfile(scratch_dir / f"fragmenstein.log", logging.ERROR)

    # os.chdir(output_path)  # needed?

    Laboratory.Victor = Wictor

    # Igor.init_pyrosetta() # needed?

    with open(protein_path) as fh:
        pdbblock: str = fh.read()

    lab = Laboratory(pdbblock=pdbblock, covalent_resi=None, run_plip=False)

    return lab
