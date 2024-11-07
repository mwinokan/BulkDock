import mrich
from pathlib import Path
import json


class BulkDock:

    def __init__(self):

        from .models import db

        self._db = db
        self._config_path = (Path(__file__).parent / "../config.json").resolve()

        self.load_config()

        mrich.h1("💪 BulkDock")

        mrich.var("input directory", self.input_dir)
        mrich.var("target directory", self.target_dir)
        mrich.var("output directory", self.output_dir)
        mrich.var("scratch directory", self.scratch_dir)

    ### PROPERTIES

    @property
    def config_path(self) -> Path:
        return self._config_path

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config: dict):

        self._config = {}

        for key, value in config.items():

            if key.startswith("DIR_"):

                path = Path(value)

                if path.is_absolute():
                    value = path
                else:
                    value = (Path(__file__).parent / value).resolve()

            self._config[key] = value

    @property
    def input_dir(self):
        return self.config["DIR_INPUT"]

    @property
    def target_dir(self):
        return self.config["DIR_TARGET"]

    @property
    def output_dir(self):
        return self.config["DIR_OUTPUT"]

    @property
    def scratch_dir(self):
        return self.config["DIR_SCRATCH"]

    @property
    def fragalysis_export_ref_url(self):
        return self.config["FRAGALYSIS_EXPORT_REF_URL"]

    @property
    def fragalysis_export_submitter_name(self):
        try:
            return self.config["FRAGALYSIS_EXPORT_SUBMITTER_NAME"]
        except KeyError:
            raise ValueError(
                "Config variable FRAGALYSIS_EXPORT_SUBMITTER_NAME not set, pass it via the CLI or set the default with the configure command"
            )

    @property
    def fragalysis_export_submitter_institution(self):
        try:
            return self.config["FRAGALYSIS_EXPORT_SUBMITTER_INSTITUTION"]
        except KeyError:
            raise ValueError(
                "Config variable FRAGALYSIS_EXPORT_SUBMITTER_INSTITUTION not set, pass it via the CLI or set the default with the configure command"
            )

    @property
    def fragalysis_export_submitter_email(self):
        try:
            return self.config["FRAGALYSIS_EXPORT_SUBMITTER_EMAIL"]
        except KeyError:
            raise ValueError(
                "Config variable FRAGALYSIS_EXPORT_SUBMITTER_EMAIL not set, pass it via the CLI or set the default with the configure command"
            )

    ### HIPPO

    def get_animal(self, target: str):

        try:
            animal_path = self.get_animal_path(target)
        except FileNotFoundError:
            return None

        target_path = self.get_target_path(target)

        try:
            import hippo
        except ImportError as e:
            mrich.error(e)
            mrich.error(
                "Could not import HIPPO, might need to run this as a SLURM job / notebook instead"
            )
            return None

        animal = hippo.HIPPO(f"{target}_bulkdock", animal_path)

        return animal

    def setup_hippo(self, target: str):

        target_path = self.get_target_path(target)
        animal = self.get_animal(target)

        mrich.print(animal)

        ### ADD HITS

        animal.add_hits(
            target_name=target,
            metadata_csv=target_path / "metadata.csv",
            aligned_directory=target_path / "aligned_files",
            load_pose_mols=True,
        )

        mrich.success(f"HIPPO set up for {target}")

    ### PLACEMENTS

    def place(
        self,
        target: str,
        infile: str,
        debug: bool = False,
        create_inspiration_sdf: bool = True,
    ):

        mrich.h2("BulkDock.place")
        mrich.var("target", target)
        mrich.var("infile", infile)

        import os
        from .io import parse_input_csv
        from .fstein import fragmenstein_place

        assert (
            self.output_dir.exists()
        ), "Output directory does not exist. Run 'create-directories' command"
        assert (
            self.scratch_dir.exists()
        ), "Scratch directory does not exist. Run 'create-directories' command"

        try:
            animal = self.get_animal(target)
        except FileNotFoundError:
            return None

        try:
            csv_path = self.get_infile_path(infile)
        except FileNotFoundError:
            return None

        data = parse_input_csv(
            animal=animal,
            file=csv_path,
            debug=debug,
        )

        SLURM_JOB_ID = os.environ["SLURM_JOB_ID"]

        assert SLURM_JOB_ID

        job_scratch_dir = self.get_scratch_subdir(SLURM_JOB_ID)

        mrich.var("job_scratch_dir", job_scratch_dir)

        pose_ids = set()

        for i, d in enumerate(data):

            mrich.h2(f"Placement task {i+1}/{len(data)}")

            compound = d["compound"]
            reference = d["reference"]
            inspirations = d["inspirations"]

            mrich.var("compound", compound)
            mrich.var("reference", reference)
            mrich.var("inspirations", inspirations.aliases)

            # create ref hits file
            if create_inspiration_sdf:
                ref_hits_path = self.create_inspiration_sdf(target, inspirations)
                mrich.var("ref_hits_path", ref_hits_path)

            # create protein file
            protein_path = reference.path.replace(".pdb", "_apo-desolv.pdb")
            mrich.var("protein_path", protein_path)

            pose_id = fragmenstein_place(
                animal=animal,
                scratch_dir=job_scratch_dir,
                compound=compound,
                reference=reference,
                inspirations=inspirations,
                protein_path=protein_path,
            )

            if pose_id:
                pose_ids.add(pose_id)

        mrich.debug("Committing changes...")
        animal.db.commit()

        if pose_ids:

            outname = infile.replace(".csv", f"_{SLURM_JOB_ID}.sdf")
            outfile = self.get_outfile_path(outname)

            poses = animal.poses[pose_ids]
            poses.write_sdf(outfile, name_col="id")

            mrich.h1(f"Determined {len(poses)} Poses\n{outfile}")
            return outfile

        else:
            mrich.error(f"Determined 0 Poses")
            return None

    def create_inspiration_sdf(self, target: str, inspirations: "PoseSet") -> "Path":

        subdir = self.get_scratch_subdir(f"{target}_inspiration_sdfs")
        sdf_path = subdir / Path("_".join(sorted(inspirations.aliases)) + ".sdf")

        if not sdf_path.exists():
            inspirations.write_sdf(sdf_path)

        return sdf_path

    def to_fragalysis(
        self,
        *,
        target: str,
        sdf_file: str,
        method: str,
        submitter_name: str | None = None,
        submitter_institution: str | None = None,
        submitter_email: str | None = None,
        ref_url: str | None = None,
        generate_pdbs: bool = False,
    ):

        mrich.h3(f"BulkDock.to_fragalysis")

        mrich.var("target", target)

        inpath = self.get_outfile_path(sdf_file)

        assert inpath.exists(), f"Input SDF does not exist: {inpath}"

        mrich.var("inpath", inpath)

        # validate fragalysis header info

        assert method, "method can not be empty"
        mrich.var("method", method)

        if not ref_url:
            ref_url = self.fragalysis_export_ref_url

        mrich.var("ref_url", ref_url)

        if not submitter_name:
            submitter_name = self.fragalysis_export_submitter_name

        mrich.var("submitter_name", submitter_name)

        if not submitter_institution:
            submitter_institution = self.fragalysis_export_submitter_institution

        mrich.var("submitter_institution", submitter_institution)

        if not submitter_email:
            submitter_email = self.fragalysis_export_submitter_email

        mrich.var("submitter_email", submitter_email)

        # get the animal

        animal = self.get_animal(target=target)

        if not animal:
            return

        # get pose IDs from SDF file

        import subprocess

        command = f'grep "RDKit          3D" -B1 {inpath.resolve()} --no-group-separator | grep -v "RDKit"'
        process = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE)
        output = process.communicate()

        pose_ids = set(int(i) for i in output[0].decode().split("\n") if i)

        poses = animal.poses[pose_ids]

        mrich.var("poses", poses)

        if generate_pdbs:
            outpath = self.get_outfile_path(
                sdf_file.replace(".sdf", "_fragalysis_wPDBs.sdf")
            )
        else:
            outpath = self.get_outfile_path(sdf_file.replace(".sdf", "_fragalysis.sdf"))

        mrich.var("outpath", outpath)

        poses.to_fragalysis(
            str(outpath.resolve()),
            ref_url=ref_url,
            method=method,
            submitter_name=submitter_name,
            submitter_institution=submitter_institution,
            submitter_email=submitter_email,
            generate_pdbs=generate_pdbs,
            name_col="id",
        )

        if generate_pdbs:
            mrich.success(f"Created Fragalysis-compatible SDF and complex PDBs")
        else:
            mrich.success(f"Created Fragalysis-compatible SDF")

    ### CONFIG

    def load_config(self):
        if self.config_path.exists():
            self.config = json.load(open(self.config_path, "rt"))
        else:
            from .config import DEFAULTS

            mrich.debug("Initialising default config")
            self.config = DEFAULTS
            self.dump_config()

    def dump_config(self):
        mrich.writing(self.config_path)
        config = self.config

        for key, value in config.items():
            if isinstance(value, Path):
                config[key] = str(value.resolve())

        json.dump(config, open(self.config_path, "wt"))

    def set_config_value(self, variable: str, value: str):
        from .config import VARIABLES

        assert variable in VARIABLES
        self.config[variable] = value
        self.dump_config()
        self.load_config()

    ### FILE LOGISTICS

    def get_target_path(self, target: str) -> Path:
        assert (
            self.target_dir.exists()
        ), "Target directory does not exist. Run 'create-directories' command"

        target = Path(target)

        target_path = self.target_dir / target.name

        if not target_path.exists():
            mrich.error("Could not find target", target, "in", self.target_dir)
            raise FileNotFoundError

        return target_path

    def get_infile_path(self, infile: str) -> Path:
        assert (
            self.input_dir.exists()
        ), "Input directory does not exist. Run 'create-directories' command"

        infile = Path(infile)

        infile_path = self.input_dir / infile.name

        if not infile_path.exists():
            mrich.error("Could not find", infile_path.name, "in", self.input_dir)
            raise FileNotFoundError

        return infile_path

    def get_outfile_path(self, outfile: str) -> Path:
        assert (
            self.output_dir.exists()
        ), "Output directory does not exist. Run 'create-directories' command"

        outfile = Path(outfile)

        outfile_path = self.output_dir / outfile.name

        return outfile_path

    def get_animal_path(self, target: str) -> Path:

        assert (
            self.target_dir.exists()
        ), "Target directory does not exist. Run 'create-directories' command"

        target = Path(target)

        target_path = self.target_dir / target.name

        if not target_path.exists():
            mrich.error("Could not find target", target, "in", self.target_dir)
            raise FileNotFoundError

        return target_path / f"{target}.sqlite"

    def create_directories(self):

        mrich.h2("BulkDock.create_directories")

        # input directory
        if not self.input_dir.exists():
            mrich.writing(self.input_dir)
            self.input_dir.mkdir()

        # TARGET directory
        if not self.target_dir.exists():
            mrich.writing(self.target_dir)
            self.target_dir.mkdir()

        # OUTPUT directory
        if not self.output_dir.exists():
            mrich.writing(self.output_dir)
            self.output_dir.mkdir()

        # SCRATCH directory
        if not self.scratch_dir.exists():
            mrich.writing(self.scratch_dir)
            self.scratch_dir.mkdir()

    def extract_target(self, target: str):

        mrich.h2("BulkDock.extract_target")
        mrich.var("target", target)

        assert (
            self.target_dir.exists()
        ), "Target directory does not exist. Run 'create-directories' command"

        zip_path = self.target_dir / f"{target}.zip"

        if not zip_path.exists():
            mrich.error("Could not find target", target, "in", self.target_dir)
            return None

        import zipfile

        with mrich.loading("Unzipping..."):
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self.target_dir / target)

        mrich.success("Done")

    def get_scratch_subdir(self, subdir_name):
        subdir = self.scratch_dir / subdir_name
        subdir.mkdir(exist_ok=True)
        return subdir