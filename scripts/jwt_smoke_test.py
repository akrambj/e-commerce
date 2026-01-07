from app.core.security import create_access_token, decode_access_token

t = create_access_token(subject="admin@admin.com")
print("token:", t[:30], "...")

p = decode_access_token(t)
print("payload:", p)
