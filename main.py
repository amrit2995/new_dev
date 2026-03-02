from logging import config
import os, sys
from sp_gen_sdk.connector.mongo import MongoConnector
from sp_gen_sdk.model import sql, workbook, report
import ddl_ingestion
import join_mapping_ingestion
import analytical_normalization


# ── MongoDB connection ───────────────────────────────────────────
# mc = MongoConnector()
# print(f"MongoDB URI: {mc.uri}")
# mc.client()

# ── Run DDL ingestion pipeline ───────────────────────────────────
# ddl_ingestion.run(mongo=mc)
# import pdb; pdb.set_trace()
ddl_query = ddl_ingestion.parse_ddl_file('/Users/amritprusty/projects/new_dev/udco-cltv/META/scripts/ddl/Analytical/ddl_f_ad_platform_campaign_social_rf_trend.sql')
print(ddl_query)

# ── Build fact → dimension join mappings ─────────────────────────
# join_mapping_ingestion.run(mongo=mc)

# ── Build normalized analytical tables/columns ───────────────────
# analytical_normalization.run(mongo=mc)

# ── Cleanup ──────────────────────────────────────────────────────
# mc.disconnect()

