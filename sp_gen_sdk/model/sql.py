import bson.binary
from sqlglot import parse_one, expressions
from pydantic import BaseModel, model_validator
from enum import Enum
from typing import Union

# Enums

class TableType(str, Enum):

    GENERIC = "GENERIC"
    DIMENSIONAL = "DIMENSIONAL"
    FACT = "FACT"
    CONFIRMED = "CONFIRMED"
    REFINED = "REFINED"

    @staticmethod
    def from_name(name: str) -> "TableType":
        if name.startswith("D1_"):
            return TableType.DIMENSIONAL
        elif name.startswith("F_") or name.startswith("FA_"):
            return TableType.FACT
        else:
            return TableType.GENERIC

class TimeGranularityType(str, Enum):
    DAY = "DAY"
    HOUR = "HOUR"
    
class DeliveryGranularityType(str, Enum):
    L1 = "CAMPAIGN"
    L2 = "LINEITEM"
    L3 = "AD"
class Purpose(str, Enum):
    DML = "DML"
    DDL = "DDL"

class Labels(BaseModel):
    key: str
    value: str

class Options(BaseModel):
    description: str
    labels: list[Labels] | None = []

class ReportMetricType(str, Enum):
    INTRADAY = "INTRADAY"     # Additive (Summable)
    CUMULATIVE = "CUMULATIVE" # Non-Additive (Last/Max)
    NON_METRIC = "NON_METRIC" # Dimensions, IDs, etc.


class ColumnType(str, Enum):

    GENERIC = "GENERIC"
    SK = "SK"                             # Surrogate key  (e.g. AD_MEDIA_CAMPAIGN_D1_SK)
    ID = "ID"                             # Natural / business identifier  (e.g. CAMPAIGN_ID)
    CD = "CD"                             # Code / short classifier  (e.g. SOURCE_APPLICATION_CD)
    NM = "NM"                             # Name / label  (e.g. CAMPAIGN_NM)
    DT = "DT"                             # Date  (e.g. AD_CAMPAIGN_START_DT)
    DW_TS = "DW_TS"                       # Data-warehouse timestamp  (DW_CREATE_TS, DW_LAST_UPDATE_TS, …)
    SRC_TS = "SRC_TS"                     # Source-system timestamp  (SOURCE_CREATED_TS, START_TS, END_TS)
    CNT = "CNT"                           # Count / metric  (e.g. CLICKS_CNT, TOTAL_CLICK_CNT)
    AMT = "AMT"                           # Monetary amount  (e.g. TOTAL_MEDIA_SPEND_AMT)
    IND = "IND"                           # Boolean indicator  (e.g. DW_LOGICAL_DELETE_IND)
    TXT = "TXT"                           # Free-text / description  (e.g. AD_CAMPAIGN_OBJECTIVE_TXT)
    DSC = "DSC"                           # Description  (e.g. ACTION_REACTION_DSC)
    SZ = "SZ"                             # Size / dimension  (e.g. PLATFORM_MEDIA_CREATIVE_SZ)
    NBR = "NBR"                           # Numeric value  (e.g. VALUE_NBR)
    DAY_ID = "DAY_ID"                     # Fiscal day identifier  (e.g. PERFORMANCE_DAY_ID)

    def all_postfixes(cls) -> set[str]:
        return set(c.value for c in cls)

    @classmethod
    def check(cls, col_name: str) -> "ColumnType":
        col_name = col_name.upper()
        postfix = col_name.split("_")[-1]
        if postfix in cls.all_postfixes():
            if postfix == 'TS':
                if col_name.startswith('DW'):
                    return cls.DW_TS
                return cls.SRC_TS
            return cls(postfix)
        return cls.GENERIC

#####################################
# Models 
#####################################

class BaseEntities(BaseModel):
    ddl_loc: str | None = None

class Query(BaseEntities):
    
    @classmethod
    def extract_file(cls, ddl_loc):
        ddl_content = ''
        with open(ddl_loc, 'r') as ddl_file:
            ddl_content = ddl_file.read()
        return ddl_content


class Property(BaseEntities):
    type: str
    value: Union[str, bool, int]

    # @classmethod
    # def parse(cls, prop_exp: expressions.Property) -> "Property":

    @classmethod
    def parse(cls, prop_exp: expressions.Property) -> dict:

        prop_type = prop_exp.this.this
        prop_value = prop_exp.args['value'].output_name

        return {
            prop_type: prop_value
        }

class Constraint(BaseEntities):
    type: str
    value: Union[str, bool, int]

    @classmethod
    def parse(cls, con_exp: expressions.Constraint) -> dict:

        if isinstance(con_exp.kind, expressions.NotNullColumnConstraint):
            return {"not_null": True}
        elif isinstance(con_exp.kind, expressions.Properties):
            for prop_exp in con_exp.kind.expressions:
                return Property.parse(prop_exp)


class Column(BaseEntities):
    name: str
    data_type: str = ''
    col_type: str = ColumnType.GENERIC
    not_null: bool = False
    # options: Options
    desc: str = ''

    @classmethod
    def constraints(cls, cons_exp) -> list:
        constraints = {}
        for cons in cons_exp:
            constraints.update(Constraint.parse(cons))
        return constraints


    @classmethod
    def parse(cls, col_def: expressions.ColumnDef) -> "Column":

        constraints = cls.constraints(col_def.constraints)
        data = {
            "name": col_def.name,
            "data_type": col_def.args.get("kind").sql(),
            "col_type": ColumnType.check(col_def.name),
            "not_null": constraints.get("not_null", False),
            "desc": constraints.get("DESCRIPTION", "")
        }

        return cls(**data)


class Granularity(BaseModel):
    delivery: str
    time: str

class AnalyticalColumn(BaseModel):
    name: str
    data_type: str = ''
    col_type: str = ColumnType.GENERIC
    not_null: bool = False
    desc: str = ''

class AnalyticalTable(BaseEntities):
    name: str = ''
    database: str = ''
    project: str = ''
    type: str = TableType.GENERIC
    metric_type: ReportMetricType = ReportMetricType.NON_METRIC
    column_names: list[str] = []
    options: Options = Options(description='', labels=[])

class Table(BaseEntities):
    name: str = ''
    database: str = ''
    project: str = ''
    type: str = TableType.GENERIC
    metric_type: ReportMetricType = ReportMetricType.NON_METRIC
    columns: list[Column] = []
    options: Options = Options(description='', labels=[])        

    @model_validator(mode='after')
    def determine_metric_type(self) -> 'Table':
        if self.type == TableType.DIMENSIONAL:
            self.metric_type = ReportMetricType.NON_METRIC
            return self

        # Check all metric-like columns
        metric_cols = [c for c in self.columns if c.col_type in (ColumnType.CNT, ColumnType.CUMULATIVE_CNT)]
        if not metric_cols:
            self.metric_type = ReportMetricType.NON_METRIC
            return self

        cumulative_count = sum(1 for c in metric_cols if c.col_type == ColumnType.CUMULATIVE_CNT)
        intraday_count = sum(1 for c in metric_cols if c.col_type == ColumnType.CNT)

        if cumulative_count > intraday_count:
            self.metric_type = ReportMetricType.CUMULATIVE
        else:
            self.metric_type = ReportMetricType.INTRADAY
        
        return self

    @classmethod
    def parse(cls, schema_expr: expressions.Table) -> "Table":

        data = {
            "name": schema_expr.this.name,
            "database": schema_expr.this.db,
            "project": schema_expr.this.catalog,
            "columns": [Column.parse(c) for c in schema_expr.expressions if isinstance(c, expressions.ColumnDef)],
            "type": TableType.from_name(schema_expr.this.name)
        }
        return cls(**data)
    

    def list_cols(self):
        return [col.name for col in self.columns]


# class Schema(BaseEntities):
#     table: Table | None = None

#     @classmethod
#     def parse(cls, schema_expr: expressions.Schema) -> "Schema":
#         data = {
#             "table": Table.parse(schema_expr.this)
#         }
#         return cls(**data)


class DDLQuery(Query):
    _query_type: str = Purpose.DDL
    table: Table | None = None
    # table: Table

    @classmethod
    def parse(cls, ddl_text: str, query_type: str = 'bigquery') -> "DDLQuery":
        expr = parse_one(ddl_text, read=query_type)

        if not isinstance(expr, expressions.Create):
            raise ValueError("Provided DDL is not a CREATE statement")

        data = {
            "table": Table.parse(expr.this)
        }

        return cls(**data)