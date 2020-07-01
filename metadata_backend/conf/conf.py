"""Python-based app configurations.

1) Database configurations
You need to specify the necessary environmental variables for connecting to
MongoDB.
Currently in use:
- MONGO_INITDB_ROOT_USERNAME - Admin username for mongodb
- MONGO_INITDB_ROOT_PASSWORD - Admin password for mongodb
- MONGODB_HOST - Mongodb server hostname, with port spesified if needed

MongoDB client should be shared across the whole application and always
imported from this module.
Admin access is needed in order to create new databases during runtime.
Default values are the same that are used in docker-compose file
found from deploy/mongodb.

2) Metadata schema types
Schema types (such as "submission", "study", "sample") are needed in
different parts of the application.

3) Mongodb query mappings
Mappings are needed to turn incoming REST api queries into mongodb queries.
Change these if database structure changes.

4) Frontend static files folder
Production version gets frontend SPA from this folder, after it has been built
and inserted here in projects Dockerfile.
"""

import json
import os
from pathlib import Path

from pymongo import MongoClient

# 1) Set up database client
mongo_user = os.getenv("MONGO_INITDB_ROOT_USERNAME", "admin")
mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "admin")
mongo_host = os.getenv("MONGODB_HOST", "localhost:27017")
url = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}"
db_client = MongoClient(url)

# 2) Load schema types and descriptions from json
path_to_schema_file = Path(__file__).parent / "schemas.json"
with open(path_to_schema_file) as schema_file:
    schema_types = json.load(schema_file)

# 3) Define mapping between url query parameters and mongodb queries
query_map = {
    "title": "title",
    "description": "description",
    "centerName": "centerName",
    "name": "name",
    "studyTitle": "descriptor.studyTitle",
    "studyType": "descriptor.studyType.attributes.existingStudyType",
    "studyAbstract": "descriptor.studyAbstract",
    "studyAttributes": {"base": "studyAttributes",
                        "keys": ["tag", "value"]},
    "sampleName": {"base": "sampleName",
                   "keys": ["taxonId", "scientificName",
                            "commonName"]},
    "scientificName": "submissionProject.organism.scientificName",
    "fileType": "dataBlock.files.file.attributes.filetype",
    "studyReference": {"base": "studyRef",
                       "keys": ["accessionId", "refname", "refcenter"]},
    "sampleReference": {"base": "sampleRef",
                        "keys": ["accessionId", "label", "refname",
                                 "refcenter"]},
    "experimentReference": {"base": "experimentRef",
                            "keys": ["accessionId", "refname",
                                     "refcenter"]},
    "runReference": {"base": "runRef",
                     "keys": ["accessionId", "refname", "refcenter"]},
    "analysisReference": {"base": "analysisRef",
                          "keys": ["accessionId", "refname",
                                   "refcenter"]},
}

# 4) Set frontend folder to be inside metadata_backend modules root
frontend_static_files = Path(__file__).parent.parent / "frontend"