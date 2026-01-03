from __future__ import annotations

import base64
import json
from functools import lru_cache
from typing import List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.core.config import get_settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class GoogleSheetsClient:
    """
    Low-level client: append rows to a configured spreadsheet.
    No Orders logic, no retries, no formatting rules.
    """

    def __init__(self, spreadsheet_id: str, sheet_name: str, service_account_info: dict):
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name

        creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        self.service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    def append_row(self, values: List[str]) -> None:
        body = {"values": [values]}
        (
            self.service.spreadsheets()
            .values()
            .append(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{self.sheet_name}'!A1",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )


def _decode_service_account_info(b64: str) -> dict:
    raw = base64.b64decode(b64.encode("utf-8"))
    return json.loads(raw.decode("utf-8"))


@lru_cache(maxsize=1)
def get_sheets_client() -> GoogleSheetsClient:
    s = get_settings()
    info = _decode_service_account_info(s.google_service_account_json_b64)

    return GoogleSheetsClient(
        spreadsheet_id=s.google_sheets_spreadsheet_id,
        sheet_name=s.google_sheets_sheet_name,
        service_account_info=info,
    )
