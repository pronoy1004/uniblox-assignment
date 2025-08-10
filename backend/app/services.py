import uuid
from typing import List, Optional, Dict
from datetime import datetime
from .models import (
    Product, Cart, CartItem, Order, DiscountCode,
    CheckoutRequest, CheckoutResponse, AdminReport, SAMPLE_PRODUCTS
)


class EcommerceService:
    """Business logic for cart, checkout, discounts, and admin report."""
    
    def __init__(self):
        self.cart: Cart = Cart()
        self.orders: List[Order] = []
        self.discount_codes: List[DiscountCode] = []
        # Make a deep copy of sample products per service instance to avoid shared state
        self.products: Dict[str, Product] = {p.id: p.copy(deep=True) for p in SAMPLE_PRODUCTS}
        self.order_counter = 0
        self.discount_nth_order = 5  # Every 5th order generates a discount
        
    def get_products(self) -> List[Product]:
        return list(self.products.values())
    
    def get_product(self, product_id: str) -> Optional[Product]:
        return self.products.get(product_id)
    
    def add_to_cart(self, product_id: str, quantity: int) -> Cart:
        """Add items to the cart with basic validation and stock updates."""
        product = self.get_product(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        
        if product.stock < quantity:
            raise ValueError(f"Insufficient stock. Available: {product.stock}")
        
        # Check if item already exists in cart
        existing_item = None
        for item in self.cart.items:
            if item.product_id == product_id:
                existing_item = item
                break
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            self.cart.items.append(
                CartItem(product_id=product_id, quantity=quantity, product=product)
            )
        
        # Update product stock then recalc totals
        product.stock -= quantity
        self.cart.calculate_totals()
        
        return self.cart
    
    def get_cart(self) -> Cart:
        return self.cart
    
    def clear_cart(self):
        # Restore product stock
        for item in self.cart.items:
            product = self.get_product(item.product_id)
            if product:
                product.stock += item.quantity
        
        self.cart = Cart()
    
    def checkout(self, request: CheckoutRequest) -> CheckoutResponse:
        """Checkout current cart, optionally applying a valid single-use discount."""
        if not self.cart.items:
            raise ValueError("Cannot checkout with empty cart")
        
        # Calculate total amount
        total_amount = self.cart.total_amount
        discount_amount = 0.0
        discount_code = None
        
        # Apply discount if provided
        if request.discount_code:
            discount_code_obj = self._validate_discount_code(request.discount_code)
            if discount_code_obj:
                discount_amount = total_amount * (discount_code_obj.discount_percentage / 100)
                # Normalize to 3 decimal places for stable comparisons
                discount_amount = round(discount_amount, 3)
                discount_code_obj.is_used = True
                discount_code_obj.used_at = datetime.now()
                discount_code = request.discount_code
            else:
                raise ValueError("Invalid or expired discount code")
        
        final_amount = round(total_amount - discount_amount, 3)
        
        # Create order
        order_id = f"order_{uuid.uuid4().hex[:8]}"
        order = Order(
            id=order_id,
            items=self.cart.items.copy(),
            total_amount=total_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            discount_code=discount_code,
            created_at=datetime.now(),
            customer_id=request.customer_id
        )
        
        # Add order to history
        self.orders.append(order)
        self.order_counter += 1
        
        # Do not auto-generate codes here; admin must generate when eligible
        
        # Clear cart after successful checkout
        self.clear_cart()
        
        return CheckoutResponse(
            order_id=order_id,
            total_amount=total_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            discount_code=discount_code,
            message="Order placed successfully!"
        )
    
    def generate_discount_code(self) -> DiscountCode:
        """Generate a discount code only when total orders is a multiple of `discount_nth_order`."""
        if self.order_counter == 0 or self.order_counter % self.discount_nth_order != 0:
            raise ValueError("Not eligible to generate discount code yet")
        return self._generate_discount_code()
    
    def _generate_discount_code(self) -> DiscountCode:
        """Internal method to generate a discount code."""
        code = f"SAVE10_{uuid.uuid4().hex[:6].upper()}"
        discount_code = DiscountCode(
            code=code,
            created_at=datetime.now()
        )
        self.discount_codes.append(discount_code)
        return discount_code
    
    def _validate_discount_code(self, code: str) -> Optional[DiscountCode]:
        """
        Validate a discount code.
        
        Args:
            code: Discount code to validate
            
        Returns:
            Discount code object if valid, None otherwise
        """
        for discount_code in self.discount_codes:
            if discount_code.code == code and not discount_code.is_used:
                return discount_code
        return None
    
    def get_analytics(self) -> AdminReport:
        """Generate admin report with totals and codes."""
        total_items_purchased = sum(
            sum(item.quantity for item in order.items) for order in self.orders
        )
        total_purchase_amount = sum(order.final_amount for order in self.orders)
        discount_codes = [code.code for code in self.discount_codes]
        total_discount_amount = sum(order.discount_amount for order in self.orders)

        return AdminReport(
            total_items_purchased=total_items_purchased,
            total_purchase_amount=total_purchase_amount,
            discount_codes=discount_codes,
            total_discount_amount=total_discount_amount,
        )


# Global service instance
ecommerce_service = EcommerceService()

