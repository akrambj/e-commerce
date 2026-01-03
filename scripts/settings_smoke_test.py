from app.core.config import get_settings

s = get_settings()
print("spreadsheet:", s.google_sheets_spreadsheet_id)
print("sheet:", s.google_sheets_sheet_name)
print("b64 length:", len(s.google_service_account_json_b64))
