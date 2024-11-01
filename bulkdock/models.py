
from datetime import datetime
from pathlib import Path
from pony.orm import *

### main tables

db = Database()

class Batch(db.Entity):
    id = PrimaryKey(int, auto=True)
    input_file = Required(str)
    target = Required('Target')
    batch_status = Required('BatchStatus')
    request = Required(datetime)
    user = Required(str)
    jobs = Set('Job')


class Target(db.Entity):
    id = PrimaryKey(int, auto=True)
    batches = Set(Batch)
    ligands = Set('Ligand')


class Ligand(db.Entity):
    id = PrimaryKey(int, auto=True)
    target = Required(Target)
    compound = Required(int)
    inspirations = Required(Json)


class Placement(db.Entity):
    id = PrimaryKey(int, auto=True)
    job = Required('Job')
    method = Optional(str)
    parameters = Optional(Json)
    pose = Optional(int)
    placement_status = Required('PlacementStatus')


class Job(db.Entity):
    id = PrimaryKey(int, auto=True)
    batch = Required(Batch)
    job_status = Required('JobStatus')
    placements = Set(Placement)


class Status(db.Entity):
    id = PrimaryKey(int, auto=True)


class BatchStatus(Status):
    batches = Set(Batch)


class JobStatus(Status):
    jobs = Set(Job)


class PlacementStatus(Status):
    placements = Set(Placement)

db.bind(provider='sqlite', filename='../bulkdock.sqlite', create_db=True)

db.generate_mapping(create_tables=True)
