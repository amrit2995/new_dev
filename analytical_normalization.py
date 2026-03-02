"""
Analytical Normalization
========================
Normalizes analytical data from 'ddl_analytical' collection into two separate 
collections: 'analytical_tables' and 'analytical_columns'.

Database   : query_builder
Collections: analytical_tables, analytical_columns
"""

from sp_gen_sdk.model.sql import AnalyticalColumn, AnalyticalTable, Table
from sp_gen_sdk.connector.mongo import MongoConnector

MONGO_DB = "query_builder"
SOURCE_COLLECTION = "ddl_analytical"
TABLES_COLLECTION = "analytical_tables"
COLUMNS_COLLECTION = "analytical_columns"

def run(mongo: MongoConnector | None = None):
    """
    Split embedded analytical data into normalized tables and columns.
    """
    own_connection = mongo is None
    if own_connection:
        mongo = MongoConnector()
        mongo.client()

    print("\n🏗️  Normalizing analytical tables and columns …\n")

    db = mongo.client()[MONGO_DB]
    
    unique_columns = {}
    normalized_tables = []

    # Step 1: Read all analytical tables
    cursor = db[SOURCE_COLLECTION].find({}, {"_id": 0, "table": 1})
    
    for doc in cursor:
        table_data = doc["table"]
        columns_data = table_data.get("columns", [])
        
        col_names = []
        for c in columns_data:
            name = c["name"]
            col_names.append(name)
            
            # Use name as key for deduplication
            if name not in unique_columns:
                unique_columns[name] = AnalyticalColumn(
                    name=name,
                    data_type=c.get("data_type", ""),
                    col_type=c.get("col_type", "GENERIC"),
                    not_null=c.get("not_null", False),
                    desc=c.get("desc", "")
                )
        
        # Create normalized table object
        norm_table = AnalyticalTable(
            name=table_data.get("name", ""),
            database=table_data.get("database", ""),
            project=table_data.get("project", ""),
            type=table_data.get("type", "GENERIC"),
            metric_type=table_data.get("metric_type", "NON_METRIC"),
            column_names=col_names,
            options=table_data.get("options", {})
        )
        normalized_tables.append(norm_table)

    print(f"  📊  Processed {len(normalized_tables)} tables")
    print(f"  📎  Extracted {len(unique_columns)} unique columns")

    # Step 2: Store in MongoDB (clean collections first)
    db[TABLES_COLLECTION].drop()
    db[COLUMNS_COLLECTION].drop()

    if unique_columns:
        col_docs = [c.model_dump() for c in unique_columns.values()]
        mongo.insert_many(MONGO_DB, COLUMNS_COLLECTION, col_docs)
        print(f"  ✓  Stored unique columns in '{COLUMNS_COLLECTION}'")

    if normalized_tables:
        table_docs = [t.model_dump() for t in normalized_tables]
        mongo.insert_many(MONGO_DB, TABLES_COLLECTION, table_docs)
        print(f"  ✓  Stored normalized tables in '{TABLES_COLLECTION}'")

    print(f"\n✅  Normalization complete.\n")

    if own_connection:
        mongo.disconnect()

if __name__ == "__main__":
    run()
