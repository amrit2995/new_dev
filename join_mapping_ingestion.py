"""
Join Mapping Ingestion
======================
Reads fact and dimension tables from MongoDB, resolves FK relationships
based on the *_D1_SK naming convention, and stores the join mappings
back into MongoDB.

Database   : query_builder
Collection : join_mappings
"""

import re
from sp_gen_sdk.model.join_mapping import JoinColumn, TableJoinMapping
from sp_gen_sdk.connector.mongo import MongoConnector

MONGO_DB = "query_builder"
MAPPINGS_COLLECTION = "join_mappings"

# Regex to identify surrogate-key FK columns in fact tables
SK_PATTERN = re.compile(r"^(.+)_D1_SK$", re.IGNORECASE)


# ── Helpers ──────────────────────────────────────────────────────

def build_dim_lookup(mongo: MongoConnector) -> dict[str, str]:
    """
    Build a lookup from surrogate-key column name → dimension table name.

    Scans all DIMENSIONAL tables across both collections and maps
    the first column (the SK column) to the table name.

    Returns e.g.:
        { "AD_MEDIA_CAMPAIGN_D1_SK": "D1_AD_MEDIA_CAMPAIGN", ... }
    """
    lookup: dict[str, str] = {}

    for coll in ["ddl", "ddl_analytical"]:
        cursor = mongo.client()[MONGO_DB][coll].find(
            {"table.type": "DIMENSIONAL"},
            {"_id": 0, "table.name": 1, "table.columns": 1},
        )
        for doc in cursor:
            table_name = doc["table"]["name"]
            columns = doc["table"].get("columns", [])
            if not columns:
                continue
            # The first column of a dimension table is its surrogate key
            sk_col = columns[0]["name"].upper()
            lookup[sk_col] = table_name

    return lookup


def resolve_fact_mappings(
    mongo: MongoConnector,
    dim_lookup: dict[str, str],
) -> list[TableJoinMapping]:
    """
    For each FACT table, find all *_D1_SK columns
    and resolve them to their matching dimension tables.
    """
    mappings: list[TableJoinMapping] = []

    for coll in ["ddl", "ddl_analytical"]:
        cursor = mongo.client()[MONGO_DB][coll].find(
            {"table.type": "FACT"},
            {"_id": 0, "table.name": 1, "table.type": 1, "table.columns": 1},
        )
        for doc in cursor:
            fact_name = doc["table"]["name"]
            fact_type = doc["table"]["type"]
            columns = doc["table"].get("columns", [])

            joins: list[JoinColumn] = []
            unresolved: list[str] = []

            for col in columns:
                col_name = col["name"].upper()
                if SK_PATTERN.match(col_name):
                    dim_table = dim_lookup.get(col_name)
                    if dim_table:
                        joins.append(JoinColumn(
                            fact_column=col_name,
                            dim_table=dim_table,
                            dim_column=col_name,
                            resolved=True,
                        ))
                    else:
                        joins.append(JoinColumn(
                            fact_column=col_name,
                            dim_table="",
                            dim_column=col_name,
                            resolved=False,
                        ))
                        unresolved.append(col_name)

            mappings.append(TableJoinMapping(
                fact_table=fact_name,
                fact_table_type=fact_type,
                joins=joins,
                unresolved=unresolved,
            ))

    return mappings


# ── Main pipeline ────────────────────────────────────────────────

def run(mongo: MongoConnector | None = None):
    """
    Build and store fact→dimension join mappings in MongoDB.
    """
    own_connection = mongo is None
    if own_connection:
        mongo = MongoConnector()
        mongo.client()

    print("\n🔗  Building fact → dimension join mappings …\n")

    # Step 1 — build SK → dimension table lookup
    dim_lookup = build_dim_lookup(mongo)
    print(f"  📖  {len(dim_lookup)} dimension surrogate keys indexed")

    # Step 2 — resolve all fact table FK columns
    mappings = resolve_fact_mappings(mongo, dim_lookup)
    print(f"  📋  {len(mappings)} fact tables analysed")

    # Step 3 — store in MongoDB (drop old collection first)
    db = mongo.client()[MONGO_DB]
    db[MAPPINGS_COLLECTION].drop()

    docs = [m.model_dump() for m in mappings]
    if docs:
        result = mongo.insert_many(MONGO_DB, MAPPINGS_COLLECTION, docs)
        print(f"  ✓  Inserted {len(result.inserted_ids)} mapping documents")

    # Summary
    total_joins = sum(len(m.joins) for m in mappings)
    total_unresolved = sum(len(m.unresolved) for m in mappings)
    print(f"\n✅  Done — {total_joins} join relationships mapped "
          f"({total_unresolved} unresolved).\n")

    # Show unresolved FKs if any
    for m in mappings:
        if m.unresolved:
            print(f"  ⚠  {m.fact_table}: unresolved → {m.unresolved}")

    if own_connection:
        mongo.disconnect()


# ── Entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    run()
