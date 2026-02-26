from sqlglot import parse_one, expressions
from pydantic import BaseModel
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

class Purpose(str, Enum):
    DML = "DML"
    DDL = "DDL"

class Labels(BaseModel):
    key: str
    value: str

class Options(BaseModel):
    description: str
    labels: list[Labels] | None = []


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
            "not_null": constraints.get("not_null", False),
            "desc": constraints.get("DESCRIPTION", "")
        }

        return cls(**data)


class Table(BaseEntities):
    name: str = ''
    database: str = ''
    project: str = ''
    type: str = TableType.GENERIC
    columns: list[Column] = []
    options: Options = Options(description='', labels=[])        

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