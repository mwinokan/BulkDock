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

Download target zip archive from fragalysis and place in TARGETS directory

```
python -m bulkdock extract TARGET_NAME
python -m bulkdock setup TARGET_NAME
```

### Placements

Place an SDF in the INPUTS directory

```
python -m bulkdock place TARGET_NAME SDF_NAME
```
