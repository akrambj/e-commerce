docker run --rm --network e-commerce_default `
  -e TEST_DATABASE_URL="postgresql://postgres:pass123@ecommerce_test_db:5432/ecommerce_test" `
  -v ${PWD}:/app -w /app `
  python:3.12-slim `
  bash -lc "pip install -r requirements.txt && pytest -q"