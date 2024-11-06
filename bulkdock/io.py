import mrich


def parse_input_csv(animal: "HIPPO", file: "Path", debug: bool = False) -> list[dict]:
    """
    Parse a BulkDock input CSV to prepare for an ensemble docking run where a compound is placed against each protein conformation from its inspirations. 

    :param animal: `HIPPO` object to work within
    :param file: `Path` object to the input CSV
    :param debug: Increase verbosity of CLI output
    :returns: a list of dictionaries containing HIPPO objects:

    compound: Compound
    reference: Pose
    inspirations: PoseSet

    """

    from pandas import read_csv

    # read dataframe from CSV
    df = read_csv(file)

    assert "smiles" in df.columns

    data = []

    for i, row in df.iterrows():

        # extract row values
        smiles = row.smiles
        inspirations = row.values[1:]

        # debug output
        if debug:
            mrich.debug("i", i)
            mrich.debug("smiles", smiles)

        # link HIPPO objects
        compound = animal.register_compound(smiles=smiles)
        inspiration_poses = animal.poses[list(inspirations)]

        # one placement against each inspiration's protein conformation
        for pose in inspiration_poses:

            # all info needed for placement
            data.append(dict(
                compound=compound,
                reference=pose,
                inspirations=inspiration_poses,
            ))

            # debug output
            if debug:
                mrich.h3("Placement")
                mrich.var("smiles", smiles)
                mrich.var("compound", compound)
                mrich.var("protein", pose.alias)
                mrich.var("inspirations", inspiration_poses.aliases)

    return data


def create_scratch_subdir(subdir_name: str) -> "Path":
    raise NotImplementedError
    