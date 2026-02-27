from logging import config
import os, sys
from sp_gen_sdk.connector.mongo import MongoConnector

WORKING_DIRECTORY = "/Users/aprus05/albertsons/amrit_rnd/sql_development_scripts/scripts/new_dev"
SDK_PARENT_LOC = os.path.join(WORKING_DIRECTORY, 'sql_development_scripts/scripts/new_dev')
sys.path.append(SDK_PARENT_LOC)


# META/config/BToA_META_D1_AD_MEDIA_PROMOTIONAL_CHANNEL_BQToBQ.json
# META/config/BToA_META_F_AD_PLATFORM_CAMPAIGN_RF_TREND_BQToBQ.json
# META/scripts/ddl/Analytical/ddl_d1_ad_media_promotional_channel.sql
# META/scripts/ddl/Analytical/ddl_f_ad_platform_campaign_rf_trend_wrk.sql
# META/scripts/ddl/Analytical/ddl_f_ad_platform_campaign_rf_trend.sql
# META/scripts/sql/META_ANALYTICAL/docs/F_AD_PLATFORM_CAMPAIGN_RF_README.md
# META/scripts/sql/META_ANALYTICAL/SP_CLTV_BIM_TO_ANALYTICS_D1_AD_MEDIA_PROMOTIONAL_CHANNEL.sql
# META/scripts/sql/META_ANALYTICAL/SP_CLTV_BIM_TO_ANALYTICS_F_AD_PLATFORM_CAMPAIGN_RF_TREND.sql
# META/scripts/views/view_f_ad_platform_campaign_rf_trend.sql

# from sp_gen_sdk import model
# from sp_gen_sdk import workbook
# from sp_gen_sdk import report

from sp_gen_sdk.model import sql, workbook, report


tables_ddl_loc_list = [
"META/scripts/ddl/Analytical/ddl_d1_ad_media_promotional_channel.sql",
"META/scripts/ddl/Analytical/ddl_f_ad_platform_campaign_rf_trend_wrk.sql",
"META/scripts/ddl/Analytical/ddl_f_ad_platform_campaign_rf_trend.sql",
"META/scripts/ddl/Analytical/ddl_f_ad_platform_campaign_rf_trend.sql",
]




WORKING_REPO_DIRECTORY = '/Users/aprus05/albertsons/udco-cltv'
WORKBOOK_LOC = "/Users/aprus05/albertsons/Ad_Platform_Campaign_Mapping_V1.3.4.1.2.xlsx"


# workbook_ap: workbook.Workbook = workbook.Workbook(WORKBOOK_LOC)




# print(f"Workbook name: {workbook.name}")
# print(f"Available sheets: {workbook_ap.sheet_names_list}")

# sheet = workbook_ap.get_sheet_by_name('Testing Sheet')
# print(f"Sheet name: {sheet.title}")
# campaign_rf: report.Report = report.Report.parse(sheet)
# print(campaign_rf.model_dump_json())
# print(f"Report name: {campaign_rf.name}")
# print(f"Report columns: {campaign_rf.col_names}")


mc = MongoConnector()
print(f"MongoDB URI: {mc.uri}")
mc.client()

# tables = []
# for ddl_rel_loc in tables_ddl_loc_list:
#     ddl_loc = os.path.join(WORKING_REPO_DIRECTORY, ddl_rel_loc)
#     print(f"Processing {ddl_loc}...")
#     query_text = sql.Query.extract_file(ddl_loc)
#     query = sql.DDLQuery.parse(query_text)
#     cols_list = query.table.list_cols()
#     print(f"Extracted columns: {cols_list}")
#     tables.append(query.model_dump_json())
#     print(f"Completed processing {ddl_loc}.\n")
# print("All tables processed. Output:")
# print(tables)