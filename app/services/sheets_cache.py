"""Google Sheets caching service for affiliate offer data."""
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Optional
from datetime import datetime, date
from models.offer import Offer
from config import Config
import json


class SheetsCacheService:
    """Reads/writes affiliate offers to Google Sheets as a daily cache."""

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    META_WORKSHEET_NAME = "_metadata"

    OFFER_COLUMNS = [
        "id", "name", "description", "network",
        "advertiser_name", "advertiser_id",
        "commission_type", "commission_value", "commission_currency",
        "epc", "conversion_rate", "avg_sale_value",
        "popularity_score", "category", "subcategory",
        "tracking_url", "landing_page_url",
        "youtube_score", "search_interest", "search_trend",
        "potential_score", "potential_rating", "potential_analysis",
        "related_keywords",
        "scalability_score", "cookie_duration", "traffic_monthly",
        "growth_percentage", "competition_level",
        "domain_authority", "instagram_followers",
    ]

    def __init__(self):
        creds = Credentials.from_service_account_file(
            Config.GOOGLE_SERVICE_ACCOUNT_JSON,
            scopes=self.SCOPES,
        )
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_url(Config.GOOGLE_SHEET_URL)

    # ------------------------------------------------------------------
    # Worksheet helpers
    # ------------------------------------------------------------------

    def _sanitize_tab_name(self, keyword: str) -> str:
        if not keyword:
            keyword = "default"
        sanitized = keyword.strip().lower()
        sanitized = sanitized.replace("/", "-").replace("\\", "-")
        sanitized = sanitized.replace("[", "(").replace("]", ")")
        return sanitized[:100]

    def _get_or_create_worksheet(self, keyword: str) -> gspread.Worksheet:
        tab_name = self._sanitize_tab_name(keyword)
        try:
            return self.spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            ws = self.spreadsheet.add_worksheet(
                title=tab_name, rows=500, cols=len(self.OFFER_COLUMNS)
            )
            ws.update([self.OFFER_COLUMNS], "A1")
            ws.format("A1:AE1", {"textFormat": {"bold": True}})
            return ws

    def _get_or_create_meta_worksheet(self) -> gspread.Worksheet:
        try:
            return self.spreadsheet.worksheet(self.META_WORKSHEET_NAME)
        except gspread.WorksheetNotFound:
            ws = self.spreadsheet.add_worksheet(
                title=self.META_WORKSHEET_NAME, rows=100, cols=2
            )
            ws.update([["keyword", "last_updated"]], "A1")
            ws.format("A1:B1", {"textFormat": {"bold": True}})
            return ws

    # ------------------------------------------------------------------
    # Timestamp / freshness
    # ------------------------------------------------------------------

    def get_last_updated(self, keyword: str) -> Optional[date]:
        meta_ws = self._get_or_create_meta_worksheet()
        tab_name = self._sanitize_tab_name(keyword)
        try:
            cell = meta_ws.find(tab_name, in_column=1)
            if cell:
                date_str = meta_ws.cell(cell.row, 2).value
                if date_str:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
        except gspread.exceptions.CellNotFound:
            pass
        return None

    def _set_last_updated(self, keyword: str, updated_date: date):
        meta_ws = self._get_or_create_meta_worksheet()
        tab_name = self._sanitize_tab_name(keyword)
        date_str = updated_date.strftime("%Y-%m-%d")
        try:
            cell = meta_ws.find(tab_name, in_column=1)
            if cell:
                meta_ws.update_cell(cell.row, 2, date_str)
            else:
                meta_ws.append_row([tab_name, date_str])
        except gspread.exceptions.CellNotFound:
            meta_ws.append_row([tab_name, date_str])

    def is_cache_fresh(self, keyword: str) -> bool:
        last_updated = self.get_last_updated(keyword)
        if last_updated is None:
            return False
        return last_updated == date.today()

    # ------------------------------------------------------------------
    # Read / Write offers
    # ------------------------------------------------------------------

    def read_offers(self, keyword: str) -> List[Offer]:
        tab_name = self._sanitize_tab_name(keyword)
        try:
            ws = self.spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            return []

        records = ws.get_all_records()
        if not records:
            return []

        offers = []
        for row in records:
            offer = self._row_to_offer(row)
            if offer:
                offers.append(offer)
        return offers

    def write_offers(self, keyword: str, offers: List[Offer]):
        ws = self._get_or_create_worksheet(keyword)

        # Clear and rewrite
        ws.clear()
        ws.update([self.OFFER_COLUMNS], "A1")

        if not offers:
            self._set_last_updated(keyword, date.today())
            return

        rows = [self._offer_to_row(o) for o in offers]
        end_col = chr(65 + len(self.OFFER_COLUMNS) - 1)  # 'A' + 30 = '_' — handled below
        # For 31 columns (A-AE) we need proper column letter mapping
        end_col_str = self._col_letter(len(self.OFFER_COLUMNS))
        end_row = len(rows) + 1
        ws.update(rows, f"A2:{end_col_str}{end_row}")

        self._set_last_updated(keyword, date.today())

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------

    FEEDBACK_WORKSHEET_NAME = "_feedback"

    def append_feedback(self, name: str, message: str):
        """Append a feedback row to the _feedback worksheet."""
        try:
            ws = self.spreadsheet.worksheet(self.FEEDBACK_WORKSHEET_NAME)
        except gspread.WorksheetNotFound:
            ws = self.spreadsheet.add_worksheet(
                title=self.FEEDBACK_WORKSHEET_NAME, rows=500, cols=3
            )
            ws.update([["timestamp", "name", "message"]], "A1")
            ws.format("A1:C1", {"textFormat": {"bold": True}})

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([timestamp, name, message])

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _col_letter(n: int) -> str:
        """Convert 1-based column number to letter (1=A, 27=AA, 31=AE)."""
        result = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def _offer_to_row(self, offer: Offer) -> list:
        row = []
        for col in self.OFFER_COLUMNS:
            value = getattr(offer, col, None)
            if value is None:
                row.append("")
            elif col == "related_keywords":
                row.append(json.dumps(value) if value else "")
            elif isinstance(value, (int, float)):
                row.append(value)
            else:
                row.append(str(value))
        return row

    @staticmethod
    def _row_to_offer(row: dict) -> Optional[Offer]:
        def to_float(val):
            if val == "" or val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        def to_int(val):
            if val == "" or val is None:
                return None
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return None

        def to_str(val):
            if val == "" or val is None:
                return None
            return str(val)

        try:
            related_keywords = None
            rk_val = row.get("related_keywords", "")
            if rk_val and rk_val != "":
                try:
                    related_keywords = json.loads(rk_val)
                except (json.JSONDecodeError, TypeError):
                    related_keywords = None

            return Offer(
                id=str(row.get("id", "")),
                name=str(row.get("name", "")),
                description=to_str(row.get("description")),
                network=str(row.get("network", "")),
                advertiser_name=str(row.get("advertiser_name", "")),
                advertiser_id=str(row.get("advertiser_id", "")),
                commission_type=to_str(row.get("commission_type")),
                commission_value=to_float(row.get("commission_value")),
                commission_currency=str(row.get("commission_currency", "USD") or "USD"),
                epc=to_float(row.get("epc")),
                conversion_rate=to_float(row.get("conversion_rate")),
                avg_sale_value=to_float(row.get("avg_sale_value")),
                popularity_score=to_float(row.get("popularity_score")),
                category=to_str(row.get("category")),
                subcategory=to_str(row.get("subcategory")),
                tracking_url=to_str(row.get("tracking_url")),
                landing_page_url=to_str(row.get("landing_page_url")),
                youtube_score=to_float(row.get("youtube_score")),
                search_interest=to_int(row.get("search_interest")),
                search_trend=to_str(row.get("search_trend")),
                potential_score=to_int(row.get("potential_score")),
                potential_rating=to_str(row.get("potential_rating")),
                potential_analysis=to_str(row.get("potential_analysis")),
                related_keywords=related_keywords,
                scalability_score=to_int(row.get("scalability_score")),
                cookie_duration=to_int(row.get("cookie_duration")),
                traffic_monthly=to_str(row.get("traffic_monthly")),
                growth_percentage=to_str(row.get("growth_percentage")),
                competition_level=to_str(row.get("competition_level")),
                domain_authority=to_int(row.get("domain_authority")),
                instagram_followers=to_str(row.get("instagram_followers")),
            )
        except Exception as e:
            print(f"Error parsing offer row: {e}")
            return None
