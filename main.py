from logging import config
import os, sys
from sp_gen_sdk.connector.mongo import MongoConnector
from sp_gen_sdk.model import sql, workbook, report
import ddl_ingestion
import join_mapping_ingestion


# ── MongoDB connection ───────────────────────────────────────────
mc = MongoConnector()
print(f"MongoDB URI: {mc.uri}")
mc.client()

# ── Run DDL ingestion pipeline ───────────────────────────────────
ddl_ingestion.run(mongo=mc)

# ── Build fact → dimension join mappings ─────────────────────────
join_mapping_ingestion.run(mongo=mc)

# ── Cleanup ──────────────────────────────────────────────────────
mc.disconnect()