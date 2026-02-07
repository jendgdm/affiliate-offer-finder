"""BigQuery YouTube SERP competitor analysis service."""
import json
from typing import List, Optional, Dict
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from config import Config


class YTSerpService:
    """Query BigQuery YT SERP data for competitor gap analysis."""

    PROJECT_ID = "company-wide-370010"
    TABLE = "`company-wide-370010.1_YT_Serp_result.ALL_Time YT Serp`"

    def __init__(self):
        sa_value = Config.GOOGLE_SERVICE_ACCOUNT_JSON
        if sa_value.strip().startswith('{'):
            info = json.loads(sa_value)
            creds = Credentials.from_service_account_info(info)
        else:
            creds = Credentials.from_service_account_file(sa_value)
        self.client = bigquery.Client(credentials=creds, project=self.PROJECT_ID)

    # Date filter used by all queries — last 7 days of tagged data
    DATE_FILTER = "Scrape_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) AND competitor_checker IS NOT NULL"

    def get_competitor_gaps(self, limit: int = 50) -> List[Dict]:
        """Find keywords competitors rank for but Digidom does NOT (last 7 days).

        Returns list of dicts with: keyword, search_volume, silo,
        num_competitors, best_rank, top_views, channels
        """
        q = f"""
        WITH cr AS (
          SELECT Keyword, Channel_title,
            MIN(Rank) as best_rank,
            MAX(Views) as top_views,
            MAX(Search_Volume) as search_volume,
            MAX(Silo) as silo
          FROM {self.TABLE}
          WHERE {self.DATE_FILTER} AND competitor_checker = 'Competitor'
          GROUP BY Keyword, Channel_title
        ),
        comp AS (
          SELECT Keyword,
            MAX(search_volume) as search_volume,
            MAX(silo) as silo,
            COUNT(*) as num_competitors,
            MIN(best_rank) as best_rank,
            MAX(top_views) as top_views,
            STRING_AGG(Channel_title || ' [' || CAST(best_rank AS STRING) || ']', ' | ' ORDER BY best_rank LIMIT 5) as channels
          FROM cr
          GROUP BY Keyword
        ),
        dg AS (
          SELECT DISTINCT Keyword
          FROM {self.TABLE}
          WHERE {self.DATE_FILTER} AND competitor_checker = 'Digidom'
        )
        SELECT comp.*
        FROM comp
        LEFT JOIN dg ON comp.Keyword = dg.Keyword
        WHERE dg.Keyword IS NULL
          AND comp.search_volume > 0
        ORDER BY comp.search_volume DESC
        LIMIT {limit}
        """
        results = []
        for row in self.client.query(q).result():
            results.append({
                "keyword": row.Keyword,
                "search_volume": row.search_volume or 0,
                "silo": row.silo or "",
                "num_competitors": row.num_competitors,
                "best_rank": row.best_rank,
                "top_views": row.top_views or 0,
                "channels": row.channels or "",
            })
        return results

    def get_competitor_outranking(self, limit: int = 50) -> List[Dict]:
        """Find keywords where competitors rank HIGHER than Digidom (last 7 days).

        Returns list of dicts with: keyword, search_volume, silo,
        dg_rank, dg_views, num_competitors, best_comp_rank,
        top_comp_views, channels
        """
        q = f"""
        WITH dg AS (
          SELECT Keyword,
            MIN(Rank) as dg_rank,
            MAX(Views) as dg_views,
            MAX(Search_Volume) as search_volume,
            MAX(Silo) as silo
          FROM {self.TABLE}
          WHERE {self.DATE_FILTER} AND competitor_checker = 'Digidom'
          GROUP BY Keyword
        ),
        cr AS (
          SELECT Keyword, Channel_title,
            MIN(Rank) as best_rank,
            MAX(Views) as top_views
          FROM {self.TABLE}
          WHERE {self.DATE_FILTER} AND competitor_checker = 'Competitor'
          GROUP BY Keyword, Channel_title
        ),
        comp AS (
          SELECT Keyword,
            COUNT(*) as num_competitors,
            MIN(best_rank) as best_comp_rank,
            MAX(top_views) as top_comp_views,
            STRING_AGG(Channel_title || ' [' || CAST(best_rank AS STRING) || ']', ' | ' ORDER BY best_rank LIMIT 5) as channels
          FROM cr
          GROUP BY Keyword
        )
        SELECT dg.Keyword as keyword, dg.search_volume, dg.silo,
               dg.dg_rank, dg.dg_views,
               comp.num_competitors, comp.best_comp_rank, comp.top_comp_views, comp.channels
        FROM dg
        JOIN comp ON dg.Keyword = comp.Keyword
        WHERE comp.best_comp_rank < dg.dg_rank
          AND dg.search_volume > 0
        ORDER BY dg.search_volume DESC
        LIMIT {limit}
        """
        results = []
        for row in self.client.query(q).result():
            results.append({
                "keyword": row.keyword,
                "search_volume": row.search_volume or 0,
                "silo": row.silo or "",
                "dg_rank": row.dg_rank,
                "dg_views": row.dg_views or 0,
                "num_competitors": row.num_competitors,
                "best_comp_rank": row.best_comp_rank,
                "top_comp_views": row.top_comp_views or 0,
                "channels": row.channels or "",
            })
        return results
