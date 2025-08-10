"""
Unit tests for the ecommerce service.
"""
import pytest
from datetime import datetime
from app.services import EcommerceService
from app.models import CheckoutRequest, AddToCartRequest


class TestEcommerceService:
    """Test cases for the EcommerceService class."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test."""
        return EcommerceService()
    
    def test_get_products(self, service):
        """Test getting all products."""
        products = service.get_products()
        assert len(products) == 5  # We have 5 sample products
        assert all(product.price > 0 for product in products)
    
    def test_get_product(self, service):
        """Test getting a specific product."""
        product = service.get_product("prod_001")
        assert product is not None
        assert product.name == "Wireless Headphones"
        assert product.price == 199.99
        
        # Test non-existent product
        product = service.get_product("non_existent")
        assert product is None
    
    def test_add_to_cart_success(self, service):
        """Test successfully adding items to cart."""
        cart = service.add_to_cart("prod_001", 2)
        assert len(cart.items) == 1
        assert cart.items[0].product_id == "prod_001"
        assert cart.items[0].quantity == 2
        assert cart.total_amount == 399.98  # 2 * 199.99
        assert cart.item_count == 2
        
        # Check stock was reduced
        product = service.get_product("prod_001")
        assert product.stock == 48  # Original 50 - 2
    
    def test_add_to_cart_existing_item(self, service):
        """Test adding more of an existing item in cart."""
        service.add_to_cart("prod_001", 1)
        cart = service.add_to_cart("prod_001", 2)
        assert len(cart.items) == 1
        assert cart.items[0].quantity == 3
        assert cart.total_amount == 599.97  # 3 * 199.99
    
    def test_add_to_cart_invalid_product(self, service):
        """Test adding non-existent product to cart."""
        with pytest.raises(ValueError, match="Product with ID non_existent not found"):
            service.add_to_cart("non_existent", 1)
    
    def test_add_to_cart_invalid_quantity(self, service):
        """Test adding invalid quantity to cart."""
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            service.add_to_cart("prod_001", 0)
        
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            service.add_to_cart("prod_001", -1)
    
    def test_add_to_cart_insufficient_stock(self, service):
        """Test adding more items than available stock."""
        with pytest.raises(ValueError, match="Insufficient stock"):
            service.add_to_cart("prod_001", 51)  # Only 50 available
    
    def test_get_cart(self, service):
        """Test getting current cart."""
        cart = service.get_cart()
        assert cart.items == []
        assert cart.total_amount == 0.0
        assert cart.item_count == 0
    
    def test_clear_cart(self, service):
        """Test clearing cart and restoring stock."""
        # Add items to cart
        service.add_to_cart("prod_001", 2)
        service.add_to_cart("prod_002", 1)
        
        # Get initial stock
        product1 = service.get_product("prod_001")
        product2 = service.get_product("prod_002")
        initial_stock1 = product1.stock
        initial_stock2 = product2.stock
        
        # Clear cart
        service.clear_cart()
        
        # Check cart is empty
        cart = service.get_cart()
        assert len(cart.items) == 0
        assert cart.total_amount == 0.0
        
        # Check stock was restored
        product1 = service.get_product("prod_001")
        product2 = service.get_product("prod_002")
        assert product1.stock == initial_stock1 + 2
        assert product2.stock == initial_stock2 + 1
    
    def test_checkout_success(self, service):
        """Test successful checkout without discount."""
        # Add items to cart
        service.add_to_cart("prod_001", 1)
        service.add_to_cart("prod_002", 2)
        
        request = CheckoutRequest()
        response = service.checkout(request)
        
        assert response.order_id.startswith("order_")
        assert response.total_amount == 249.97  # 199.99 + (2 * 24.99)
        assert response.discount_amount == 0.0
        assert response.final_amount == 249.97
        assert response.discount_code is None
        assert "successfully" in response.message.lower()
        
        # Check cart is cleared
        cart = service.get_cart()
        assert len(cart.items) == 0
    
    def test_checkout_empty_cart(self, service):
        """Test checkout with empty cart."""
        request = CheckoutRequest()
        with pytest.raises(ValueError, match="Cannot checkout with empty cart"):
            service.checkout(request)
    
    def test_checkout_with_discount(self, service):
        """Test checkout with valid discount code."""
        # Make eligible for discount generation and generate code
        service.discount_nth_order = 1
        service.add_to_cart("prod_001", 1)
        service.checkout(CheckoutRequest())
        discount_code = service.generate_discount_code()

        # Add items to cart and checkout with discount
        service.add_to_cart("prod_001", 1)
        request = CheckoutRequest(discount_code=discount_code.code)
        response = service.checkout(request)

        assert response.discount_amount == 19.999  # 10% of 199.99
        assert response.final_amount == 179.991  # 199.99 - 19.999
        assert response.discount_code == discount_code.code
        # Check discount code is marked as used
        assert discount_code.is_used is True
        assert discount_code.used_at is not None
    
    def test_checkout_invalid_discount(self, service):
        """Test checkout with invalid discount code."""
        service.add_to_cart("prod_001", 1)
        
        request = CheckoutRequest(discount_code="INVALID_CODE")
        with pytest.raises(ValueError, match="Invalid or expired discount code"):
            service.checkout(request)
    
    def test_discount_code_generation(self, service):
        """Test discount code generation."""
        service.discount_nth_order = 1
        service.add_to_cart("prod_001", 1)
        service.checkout(CheckoutRequest())
        discount_code = service.generate_discount_code()
        
        assert discount_code.code.startswith("SAVE10_")
        assert len(discount_code.code) == 13  # "SAVE10_" + 8 chars
        assert discount_code.discount_percentage == 10.0
        assert discount_code.is_used is False
        assert discount_code.created_at is not None
    
    
    
    def test_validate_discount_code(self, service):
        """Test discount code validation."""
        # Generate a discount code after eligibility
        service.discount_nth_order = 1
        service.add_to_cart("prod_001", 1)
        service.checkout(CheckoutRequest())
        discount_code = service.generate_discount_code()
        
        # Test valid code
        validated = service._validate_discount_code(discount_code.code)
        assert validated is not None
        assert validated.code == discount_code.code
        
        # Test invalid code
        validated = service._validate_discount_code("INVALID")
        assert validated is None
        
        # Test used code
        discount_code.is_used = True
        validated = service._validate_discount_code(discount_code.code)
        assert validated is None
    
    def test_no_auto_discount_generation(self, service):
        """Codes are not auto-generated on checkout."""
        service.discount_nth_order = 3
        service.add_to_cart("prod_001", 1)
        service.checkout(CheckoutRequest())
        service.add_to_cart("prod_002", 1)
        service.checkout(CheckoutRequest())
        service.add_to_cart("prod_003", 1)
        service.checkout(CheckoutRequest())
        assert len(service.discount_codes) == 0
    
    def test_get_analytics(self, service):
        """Test admin report generation."""
        service.add_to_cart("prod_001", 1)
        service.checkout(CheckoutRequest())
        service.add_to_cart("prod_002", 2)
        service.checkout(CheckoutRequest())
        report = service.get_analytics()
        assert report.total_items_purchased == 3
        assert report.total_purchase_amount > 0
        assert isinstance(report.discount_codes, list)
        assert report.total_discount_amount >= 0
    
    def test_analytics_with_discounts(self, service):
        """Test report when discounts are used."""
        service.discount_nth_order = 1
        service.add_to_cart("prod_001", 1)
        service.checkout(CheckoutRequest())
        discount_code = service.generate_discount_code()
        service.add_to_cart("prod_001", 1)
        service.checkout(CheckoutRequest(discount_code=discount_code.code))
        report = service.get_analytics()
        assert report.total_discount_amount > 0


