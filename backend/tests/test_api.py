"""
Integration tests for the FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import ecommerce_service

client = TestClient(app)


class TestProductsAPI:
    """Test product endpoints."""
    def test_products_omitted(self):
        response = client.get("/api/v1/products")
        assert response.status_code in (404, 405)


class TestCartAPI:
    """Test cases for cart-related endpoints."""
    
    def test_add_to_cart_success(self):
        """Test successfully adding item to cart."""
        data = {"product_id": "prod_001", "quantity": 2}
        response = client.post("/api/v1/cart/add", json=data)
        assert response.status_code == 200
        
        cart = response.json()
        assert len(cart["items"]) == 1
        assert cart["items"][0]["product_id"] == "prod_001"
        assert cart["items"][0]["quantity"] == 2
        assert cart["total_amount"] == 399.98
    
    def test_add_to_cart_invalid_product(self):
        """Test adding non-existent product to cart."""
        data = {"product_id": "non_existent", "quantity": 1}
        response = client.post("/api/v1/cart/add", json=data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_add_to_cart_invalid_quantity(self):
        """Test adding invalid quantity to cart."""
        data = {"product_id": "prod_001", "quantity": 0}
        response = client.post("/api/v1/cart/add", json=data)
        assert response.status_code == 400
        assert "greater than 0" in response.json()["detail"].lower()
    
    def test_get_cart(self):
        """Test getting current cart."""
        response = client.get("/api/v1/cart")
        assert response.status_code == 200
        
        cart = response.json()
        assert "items" in cart
        assert "total_amount" in cart
        assert "item_count" in cart
    
    def test_clear_cart(self):
        """Test clearing cart."""
        # First add items to cart
        client.post("/api/v1/cart/add", json={"product_id": "prod_001", "quantity": 1})
        
        # Then clear cart
        response = client.delete("/api/v1/cart/clear")
        assert response.status_code == 200
        assert "cleared" in response.json()["message"].lower()
        
        # Verify cart is empty
        cart_response = client.get("/api/v1/cart")
        cart = cart_response.json()
        assert len(cart["items"]) == 0


class TestCheckoutAPI:
    """Test cases for checkout endpoint."""
    
    def test_checkout_success(self):
        """Test successful checkout without discount."""
        # Add items to cart first
        client.post("/api/v1/cart/add", json={"product_id": "prod_001", "quantity": 1})
        
        response = client.post("/api/v1/checkout", json={})
        assert response.status_code == 200
        
        result = response.json()
        assert "order_id" in result
        assert result["total_amount"] == 199.99
        assert result["discount_amount"] == 0.0
        assert result["final_amount"] == 199.99
        assert "successfully" in result["message"].lower()
    
    def test_checkout_empty_cart(self):
        """Test checkout with empty cart."""
        response = client.post("/api/v1/checkout", json={})
        assert response.status_code == 400
        assert "empty cart" in response.json()["detail"].lower()
    
    def test_checkout_with_discount_not_eligible(self):
        """Generating code before eligibility should fail."""
        r = client.post("/api/v1/admin/discount/generate")
        assert r.status_code == 400
    
    def test_checkout_invalid_discount(self):
        """Test checkout with invalid discount code."""
        # Add items to cart
        client.post("/api/v1/cart/add", json={"product_id": "prod_001", "quantity": 1})
        
        response = client.post("/api/v1/checkout", json={"discount_code": "INVALID"})
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


class TestDiscountAPI:
    """Test discount request endpoint."""
    def test_discount_request_missing(self):
        response = client.get("/api/v1/discount/request")
        assert response.status_code in (404, 405)


class TestAdminAPI:
    """Test cases for admin endpoints."""
    
    def test_generate_discount_code(self):
        """Test generating discount code."""
        # Make eligible by setting nth=1 and placing one order
        ecommerce_service.discount_nth_order = 1
        client.post("/api/v1/cart/add", json={"product_id": "prod_001", "quantity": 1})
        client.post("/api/v1/checkout", json={})
        response = client.post("/api/v1/admin/discount/generate")
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert "discount_code" in result
        assert result["discount_code"].startswith("SAVE10_")
        assert "created_at" in result
    
    def test_get_analytics(self):
        """Test admin report shape."""
        response = client.get("/api/v1/admin/analytics")
        assert response.status_code == 200
        result = response.json()
        assert set(result.keys()) == {
            "total_items_purchased",
            "total_purchase_amount",
            "discount_codes",
            "total_discount_amount",
        }


class TestRootEndpoints:
    """Test cases for root endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert "version" in result
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "healthy"
        assert result["service"] == "ecommerce-api"

