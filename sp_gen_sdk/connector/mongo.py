import pymongo

class MongoConnector:
    def __init__(self, uri: str = "mongodb://localhost:27017"):
        self._uri = uri
        self._client = None

    @property
    def uri(self ) -> str:
        return self._uri

    def client(self):
        if not self._client:
            self._create_client()
            print(f"Connected to MongoDB at {self.uri}")
        return self._client

    def _create_client(self, uri: str = None):
        if uri:
            self._uri = uri
        self._client = pymongo.MongoClient(self.uri)

    def disconnect(self):
        if self._client:
            self._client.close()
            self._client = None

    def execute_query(self, db_name: str, collection_name: str, query: dict):
        if not self._client:
            raise Exception("Not connected to MongoDB")
        db = self._client[db_name]
        collection = db[collection_name]
        return list(collection.find(query))

    def insert_one(self, db_name: str, collection_name: str, document: dict):
        if not self._client:
            raise Exception("Not connected to MongoDB")
        db = self._client[db_name]
        collection = db[collection_name]
        return collection.insert_one(document)

    def insert_many(self, db_name: str, collection_name: str, documents: list[dict]):
        if not self._client:
            raise Exception("Not connected to MongoDB")
        db = self._client[db_name]
        collection = db[collection_name]
        return collection.insert_many(documents)