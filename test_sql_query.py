import sqlglot
from sqlglot import parse_one, expressions

# import pdb;pdb.set_trace()
# sql = "SELECT a.id, b.name FROM users a JOIN accounts b ON a.acc_id = b.id WHERE a.active = 1"

sql = '''
CREATE OR REPLACE TABLE `<<CLTV_PROJECT_ID>>.<<ANALYTIC_DATASET>>.D1_AD_MEDIA_PROMOTIONAL_CHANNEL`
(
	AD_MEDIA_PROMOTIONAL_CHANNEL_D1_SK NUMERIC NOT NULL,
	PLATFORM_PROMOTIONAL_CHANNEL_CD STRING NOT NULL OPTIONS(DESCRIPTION = "Unique values from platform promotional channel: Display, On-Site Display, On-Site SPA, Social, Digital Instore, CTV, High Impact Display, PromoAmp, Email"),
	DW_CREATE_TS TIMESTAMP NOT NULL,
	DW_LAST_UPDATE_TS TIMESTAMP NOT NULL
)
OPTIONS(
	DESCRIPTION = "This table holds all possible values for advertisement channel valid for different platforms like Meta, Pinterest, GAM, DV360, Instore, Criteo, Undertone, etc.",
	labels = [('appcode','uddi'),('bodname','meta'),('domainname','collect'),('environment','<<ENV>>')]
);
'''


expr = parse_one(sql, read="bigquery")  # or "postgres", "snowflake", etc.
# Inspect the AST
print(expr)                 # prints a tree-like SQL expression
print(expr.find_all(expressions.Column))  # iterate over Column nodes

# Extract table names
import pdb;pdb.set_trace()
tables = [t.name for t in expr.find_all(expressions.Table)]
print(tables)  # ['users', 'accounts']

# Extract selected columns
select_cols = [c.alias_or_name for c in expr.select.expressions]
print(select_cols)  # ['id', 'name']