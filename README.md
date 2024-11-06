# BulkDock
💪 BulkDock: Manage batches of Fragmenstein restrained protein-ligand docking jobs 

## Usage

Clone the repo on IRIS and change to directory:

```
git clone git@github.com:mwinokan/BulkDock
cd BulkDock
```

### Configure

Configure variables

```
python -m bulkdock configure
```

### Create directories

```
python -m bulkdock create-directories
```

### Setup target

First download a target zip archive from fragalysis and place in TARGETS directory.

Extract the target:

```
python -m bulkdock extract TARGET_NAME
```

Setup the HIPPO database **from within a valid SLURM job**:

```
python -m bulkdock setup TARGET_NAME
```

On IRIS this can be achieved with:

```
sb.sh --job-name "BULKDOCK_SETUP" /opt/xchem-fragalysis-2/maxwin/slurm/run_python.sh -m bulkdock setup TARGET_NAME
```

### Placements

Place a CSV in the INPUTS directory with the following structure:

|           smiles            | inspiration 1 | inspiration 2 |
|-----------------------------|---------------|---------------|
| CC(=O)Nc1ccccc1CCS(N)(=O)=O | A0487a        | A0719a        |

**The `smiles` column is required and must come first. The name of the other columns is not used, but values in those columns must refer to the observation shortcode of any inspiration hits for this compound**

The command that needs to run **from within a valid SLURM job** is:

```
python -m bulkdock place TARGET_NAME SDF_NAME
```

On IRIS this can be achieved with:

```
sb.sh --job-name "BULKDOCK_PLACE" /opt/xchem-fragalysis-2/maxwin/slurm/run_python.sh -m bulkdock place TARGET_NAME SDF_NAME
```
