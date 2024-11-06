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

    def place(self, target: str, infile: str, debug: bool = False):

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

        job_scratch_dir = self.create_scratch_subdir(SLURM_JOB_ID)

        mrich.debug("job_scratch_dir", job_scratch_dir)

        for d in data:

            mrich.debug(d)

            result = fragmenstein_place(
                scratch_dir=job_scratch_dir,
                smiles=smiles,
                protein_path=protein_path,
                ref_hits_path=ref_hits_path,
            )

        raise NotImplementedError

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

        target_path = self.target_dir / target

        if not target_path.exists():
            mrich.error("Could not find target", target, "in", self.target_dir)
            raise FileNotFoundError

        return target_path

    def get_infile_path(self, infile: str) -> Path:
        assert (
            self.input_dir.exists()
        ), "Input directory does not exist. Run 'create-directories' command"

        infile_path = self.input_dir / infile

        if not infile_path.exists():
            mrich.error("Could not find", infile_path.name, "in", self.input_dir)
            raise FileNotFoundError

        return infile_path

    def get_animal_path(self, target: str) -> Path:

        assert (
            self.target_dir.exists()
        ), "Target directory does not exist. Run 'create-directories' command"

        target_path = self.target_dir / target

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


    def create_scratch_subdir(self, subdir_name):
        subdir = self.scratch_dir / subdir_name
        subdir.mkdir()
        return subdir
