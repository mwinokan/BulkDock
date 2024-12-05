import mrich


def split_input_csv(in_path: "Path", split: int, out_dir: "Path") -> "list[Path]":

    mrich.h3("bulkdock.io.split_input_csv()")
    mrich.var("input", in_path)
    mrich.var("output", out_dir)
    mrich.var("batch size", split)

    from pandas import read_csv

    # read dataframe from CSV
    df = read_csv(in_path)

    mrich.var("#compounds", len(df))

    dfs = [df[i : i + split] for i in range(0, df.shape[0], split)]

    mrich.var("#batches", len(dfs))

    paths = []

    for i, df in enumerate(dfs):

        out_file = in_path.name.removesuffix(".csv") + f"_split{split}_batch{i:03}.csv"

        out_path = out_dir / out_file

        mrich.writing(out_path)
        df.to_csv(out_path, index=False)
        paths.append(out_path)

    return paths


def parse_input_csv(
    animal: "HIPPO",
    file: "Path",
    debug: bool = False,
    reference: str | None = None,
) -> list[dict]:
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

    mrich.h1("Compound Registration")
    values = animal.register_compounds(smiles=df["smiles"].values)

    inchikeys = [inchikey for inchikey, smiles in values]

    data = []

    mrich.h1("Placements")

    for (i, row), inchikey in zip(df.iterrows(), inchikeys):

        # extract row values
        smiles = row.smiles
        inspirations = row.values[1:]

        compound = animal.db.get_compound(inchikey=inchikey)
        assert compound

        # debug output
        if debug:
            mrich.debug("i", i)
            mrich.debug("smiles", smiles)

        inspirations = [i for i in inspirations if isinstance(i, str) and i]

        try:
            inspiration_poses = animal.poses[list(inspirations)]
        except Exception as e:
            mrich.error(e)
            mrich.error(f"Could not find get {inspirations=}")
            continue

        if not reference:

            # one placement against each inspiration's protein conformation
            for pose in inspiration_poses:

                # all info needed for placement
                data.append(
                    dict(
                        compound=compound,
                        reference=pose,
                        inspirations=inspiration_poses,
                    )
                )

                # debug output
                if debug:
                    mrich.h3("Placement")
                    mrich.var("smiles", smiles)
                    mrich.var("inchikey", inchikey)
                    mrich.var("compound", compound)
                    mrich.var("protein", pose.alias)
                    mrich.var("inspirations", inspiration_poses.aliases)

        else:

            reference_pose = animal.poses[reference]

            # all info needed for placement
            data.append(
                dict(
                    compound=compound,
                    reference=reference_pose,
                    inspirations=inspiration_poses,
                )
            )

            # debug output
            if debug:
                mrich.h3("Placement")
                mrich.var("smiles", smiles)
                mrich.var("inchikey", inchikey)
                mrich.var("compound", compound)
                mrich.var("protein", pose.alias)
                mrich.var("inspirations", inspiration_poses.aliases)

    return data


def mols_to_sdf(mols, out_path):

    from rdkit.Chem import Mol
    from rdkit.Chem import PandasTools
    from pandas import DataFrame

    data = []
    for i, mol in enumerate(mols):
        data.append({"_Name": f"mol{i}", "ROMol": Mol(mol)})

    df = DataFrame(data)
    PandasTools.WriteSDF(df, out_path, "ROMol", "_Name", list(df.columns))
