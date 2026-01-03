from app.infrastructure.integrations.google_sheets import get_sheets_client

client = get_sheets_client()
client.append_row(["smoke_test", "hello", "123"])
print("✅ appended to sheet")
