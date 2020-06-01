"""Services that handle database connections. Implemented with MongoDB.

MongoDB client should be shared across the whole application, so it's created
here as module level variable.

Admin access is needed in order to create new databases during runtime.
Default values are the same that are used in docker-compose file
found from deploy/mongodb.
"""

import os
from typing import Dict

from pymongo import MongoClient, errors
from pymongo.cursor import Cursor

# Set up database client
mongo_user = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "admin")
mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "admin")
mongo_host = os.getenv("MONGODB_HOST", "localhost:27017")
url = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}"
db_client = MongoClient(url)


class DBService:
    """Create database service used to communicate with database.

    With this class, it is possible to create separate databases for different
    purposes (e.g. submissions and backups).

    All services should use the same client, since pymongo handles pooling
    automatically.
    """

    def __init__(self, database_name: str) -> None:
        """Create service for given database.

        Service will have read-write access to given database. Database will be
        created during first read-write operation if not already present.
        :param database_name: Name of database to be used
        """
        self.database = db_client[database_name]


class CRUDService:
    """Static methods to handle CRUD operations."""

    @staticmethod
    def create(db_service: DBService, collection: str, document: Dict) -> None:
        """Insert document to collection in database.

        :param db_service: Service that connects to database
        :param collection: Collection where document should be inserted
        :param document: Document to be inserted
        :raises: Error when write fails for any Mongodb related reason
        """
        try:
            db_service.database[collection].insert_one(document)
        except errors.PyMongoError:
            raise

    @staticmethod
    def read(db_service: DBService, collection: str,
             query: Dict) -> Cursor:
        """Insert document to collection in database.

        :param db_service: Database object which connect to MongoDB database
        :param collection: Collection where document should be searched from
        :param query: Query for document(s) that should be found
        :returns: Pymongo's Cursor object (iterator)
        :raises: Error when read fails for any Mongodb related reason
        """
        try:
            return db_service.database[collection].find(query)
        except errors.ConnectionFailure:
            raise
