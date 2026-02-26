from os import rename

from pydantic import BaseModel
from enum import Enum
from typing import Mapping, Union
from sp_gen_sdk.model import workbook
import pandas as pd
import re
from pydantic import validator  


# class 
# Column Name	Data Type	Column Description	Source Table	Source Column	Transformation	Target analytical Table	Target analytical Column				
class ColMap(BaseModel):
    name: str
    table: str


class StageMapping(BaseModel):
# Column Name	Data Source Field 	Column Description	Example	Confirmed Layer Table Name	Confirmed Layer Column Name	Raw_col_name	Transformation Logic 	Anlalytical Table name	Anlalytical Column Name 	Comments	META APPLICABLE. IF Not Y Default to -1	DV360 APPLICABLE. IF Not Y Default to -1	

    column_name: str
    data_source_field: str
    column_description: str
    example: str
    confirmed_layer_table_name: str
    confirmed_layer_column_name: str
    raw_col_name: str
    transformation_logic: str
    analytical_table_name: str
    analytical_column_name: str
    comments: str
    meta_applicable: Union[str, int]
    dv360_applicable: Union[str, int]

    @validator('meta_applicable', 'dv360_applicable', pre=True, always=True)
    def if_nan(cls, v):
        if isinstance(v, float) and pd.isna(v):
            return 'NA'
        return v

class ReportMapping(BaseModel):
    column_name: str
    data_type: str
    column_description: str
    source_column: str
    source_table: str
    transformation: str
    target_table: str
    target_column: str

    @validator('transformation', 'source_column', 'source_table', 'target_table', 'target_column', pre=True, always=True)
    def if_nan(cls, v):
        if isinstance(v, float) and pd.isna(v):
            return 'NA'
        return v

class GenericMappingSheet(BaseModel):
    name: str
    _worksheet: workbook.Spreadsheet
    
    # def __init__(self, worksheet: workbook.Spreadsheet):
    #     self._worksheet: workbook.Spreadsheet = worksheet
    #     self.col_names = self.get_cols()

    def identify_cols(self):
        cols = self._worksheet.get_all_cols()
        return cols
    
    @classmethod
    def to_pandas(cls, worksheet: workbook.Spreadsheet):

        columns = worksheet.get_all_cols()
        data = []
        for row in worksheet.iter_rows():
            data.append(row)
        df = pd.DataFrame(data, columns=columns)
        return df


    @classmethod
    def rename_df(cls, df: pd.DataFrame):

        def map_col_names(original_cols, final_cols):
            rename_col_map = {}
            for final_col in final_cols:
                for original_col in original_cols:
                    final_col_set = set(final_col.lower().split('_'))
                    original_col_set = set(original_col.lower().split(' '))
                    if final_col_set.issubset(original_col_set) or original_col_set.issubset(final_col_set):
                        # rename_col_map[final_col] = original_col
                        rename_col_map[original_col] = final_col
            return rename_col_map

        final_cols = ReportMapping.__fields__.keys()
        # original_cols = df.columns.tolist()
        original_cols = [col for col in df.columns.tolist() if isinstance(col, str) and col and col[0].isalpha() and str(col).lower() != 'nan']
        col_map = map_col_names(original_cols, final_cols)

        df.rename(columns=col_map, inplace=True)
        import pdb;pdb.set_trace()
        df = df[list(final_cols)]

        return df

    @classmethod
    def parse(cls, worksheet: workbook.Spreadsheet):
        
        df = cls.to_pandas(worksheet)
        df = cls.rename_df(df)


        final_cols = ReportMapping.__fields__.keys()

        mappings = []
        
        for row in df.itertuples(index=False):
            row_dict = row._asdict()
            print(row)
            mapping_data = {col: row_dict.get(col, None) for col in final_cols}
            mapping = ReportMapping(**mapping_data)
            mappings.append(mapping)


        print(df.head(5))

        # for row in df.itertuples(index=False):
        #     mappings.append(Mapping(**{col: row._asdict().get(col, None) for col in final_cols}))
        
        return cls(name=worksheet.title, _worksheet=worksheet, mappings=mappings)

        # for mapping in worksheet.iter_rows():
        #     import pdb;pdb.set_trace()


        # mappings = [
        #     Mapping(
        #         column_name=col,
        #         data_type="STRING",
        #         column_description="",
        #         source=ColMap(name=col, table=""),
        #         transformation="",
        #         target=ColMap(name=col, table="")
        #     )
        #     for col  in worksheet.get_all_rows()
        # ]
        # return cls(name=worksheet.title, _worksheet=worksheet)


    @property
    def name(self):
        return self._worksheet.title
    
    def get_cols(self):
        rows = self._worksheet.get_all_rows()
        cols = rows[1]
        return cols
    
class Report(GenericMappingSheet):
    mappings: list[ReportMapping] = []
    
class StageMap(GenericMappingSheet):
    mappings: list[StageMapping] = []
