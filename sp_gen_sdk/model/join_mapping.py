from pydantic import BaseModel


class JoinColumn(BaseModel):
    """A single foreign-key relationship between a fact column and a dimension table."""
    fact_column: str          # e.g. "AD_MEDIA_CAMPAIGN_D1_SK"
    dim_table: str            # e.g. "D1_AD_MEDIA_CAMPAIGN"
    dim_column: str           # e.g. "AD_MEDIA_CAMPAIGN_D1_SK"
    resolved: bool = True     # False if no matching dimension table was found


class TableJoinMapping(BaseModel):
    """Join mapping for a single fact table to all its related dimension tables."""
    fact_table: str                    # e.g. "F_AD_PLATFORM_CAMPAIGN_TREND"
    fact_table_type: str               # e.g. "FACT"
    joins: list[JoinColumn] = []       # resolved FK → dimension mappings
    unresolved: list[str] = []         # FK columns with no matching dimension table

    def join_sql(self, fact_alias: str = "f") -> str:
        """
        Generate a SQL JOIN clause fragment for all resolved dimension joins.

        Example output:
            JOIN `D1_AD_MEDIA_CAMPAIGN` AS d1 ON f.AD_MEDIA_CAMPAIGN_D1_SK = d1.AD_MEDIA_CAMPAIGN_D1_SK
            JOIN `D1_PLATFORM_ADVERTISER` AS d2 ON f.PLATFORM_ADVERTISER_D1_SK = d2.PLATFORM_ADVERTISER_D1_SK
        """
        lines = []
        for i, j in enumerate(self.joins, start=1):
            if not j.resolved:
                continue
            alias = f"d{i}"
            lines.append(
                f"JOIN `{j.dim_table}` AS {alias} "
                f"ON {fact_alias}.{j.fact_column} = {alias}.{j.dim_column}"
            )
        return "\n".join(lines)
