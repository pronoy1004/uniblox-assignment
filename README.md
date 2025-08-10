## Ecommerce Store API (Minimal Implementation)

This project implements an ecommerce store with the following features:

- In-memory shopping cart (no database)
- Checkout that optionally applies a single-use 10% discount code
- Discount codes are created by an admin only when eligible (every nth order)
- Minimal admin analytics (counts and totals only)

### How it maps to the assignment

- “Add items to cart” → POST `/api/v1/cart/add`
- “Checkout with discount validation” → POST `/api/v1/checkout`
- “Every nth order gets a 10% coupon” → Admin can create a code only when the store has reached an eligible order count (nth). The code is single-use and applies to the entire order.
- “Admin APIs” →
  - POST `/api/v1/admin/discount/generate` (gated by eligibility)
  - GET `/api/v1/admin/analytics` (minimal report)


---

## Run locally

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Swagger UI: `http://localhost:8000/docs`

---

## API walkthrough (typical flow)

1) Add items to cart
```json
POST /api/v1/cart/add
{
  "product_id": "prod_001",
  "quantity": 2
}
```

2) Check cart contents
```
GET /api/v1/cart
```

3) Checkout (without discount)
```
POST /api/v1/checkout
{}
```

4) Generate a discount code (admin) when eligible
- Eligibility is based on total number of orders placed so far being a multiple of `n` (default 5).
- If not yet eligible, this endpoint returns 400 with a clear message.
```
POST /api/v1/admin/discount/generate
```
Response includes the generated code (format `SAVE10_XXXXXX`).

5) Use a discount code on checkout
```json
POST /api/v1/checkout
{
  "discount_code": "SAVE10_XXXXXX"
}
```

6) Minimal admin analytics
```
GET /api/v1/admin/analytics
```
Returns:
```json
{
  "total_items_purchased": 12,
  "total_purchase_amount": 1234.56,
  "discount_codes": ["SAVE10_ABC123", "SAVE10_DEF456"],
  "total_discount_amount": 78.9
}
```

---

## Business rules and error handling

- Cart is in-memory and process-local. Server restarts reset all state.
- Add to cart validates the product ID exists, quantity > 0, and there is sufficient stock.
- Checkout requires a non-empty cart. If a `discount_code` is supplied, it must exist and be unused; otherwise checkout returns 400.
- Discount code is single-use and applies 10% to the entire pre-discount order total.
- Admin code generation is rejected (400) if the store hasn’t yet reached an eligible order count (every nth order).
- Amounts are rounded consistently to ensure deterministic tests.

---

## Data model (high level)

- Cart: list of cart items, `total_amount`, `item_count`.
- Order: line items, `total_amount`, `discount_amount`, `final_amount`, optional `discount_code`, `created_at`.
- DiscountCode: string code, 10% rate, `is_used`, timestamps.
- Admin analytics (minimal):
  - `total_items_purchased`
  - `total_purchase_amount`
  - `discount_codes` (all generated codes)
  - `total_discount_amount`

---


## Tests

Unit and integration tests cover the shopping cart, checkout with/without discounts, eligibility-gated discount generation, and the admin analytics report.

Run tests:
```bash
cd backend
pytest -q
```

---

## What’s not included 

- Persistent storage, authentication/authorization, multi-user carts, or a public endpoint to “request” a discount code.
- Broader reporting (averages, recent orders, active codes list) beyond what the assignment strictly requires.
