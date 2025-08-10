from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    HOME = "home"
    SPORTS = "sports"


class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float = Field(gt=0, description="Product price in USD")
    category: ProductCategory
    stock: int = Field(ge=0, description="Available stock quantity")
    image_url: Optional[str] = None


class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, description="Quantity of the product")
    product: Product  # Full product details


class Cart(BaseModel):
    items: List[CartItem] = []
    total_amount: float = 0.0
    item_count: int = 0

    def calculate_totals(self):
        self.total_amount = sum(item.quantity * item.product.price for item in self.items)
        self.item_count = sum(item.quantity for item in self.items)


class DiscountCode(BaseModel):
    code: str
    discount_percentage: float = 10.0  # 10% discount
    is_used: bool = False
    created_at: datetime
    used_at: Optional[datetime] = None
    order_id: Optional[str] = None


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Order(BaseModel):
    id: str
    items: List[CartItem]
    total_amount: float
    discount_amount: float = 0.0
    final_amount: float
    discount_code: Optional[str] = None
    status: OrderStatus = OrderStatus.CONFIRMED
    created_at: datetime
    customer_id: Optional[str] = None


class CheckoutRequest(BaseModel):
    discount_code: Optional[str] = None
    customer_id: Optional[str] = None


class CheckoutResponse(BaseModel):
    order_id: str
    total_amount: float
    discount_amount: float
    final_amount: float
    discount_code: Optional[str] = None
    message: str


class AddToCartRequest(BaseModel):
    product_id: str
    quantity: int


class AdminReport(BaseModel):
    total_items_purchased: int
    total_purchase_amount: float
    discount_codes: List[str]
    total_discount_amount: float


# Sample product catalog
SAMPLE_PRODUCTS = [
    Product(
        id="prod_001",
        name="Wireless Headphones",
        description="High-quality wireless headphones with noise cancellation",
        price=199.99,
        category=ProductCategory.ELECTRONICS,
        stock=50,
        image_url="https://example.com/headphones.jpg"
    ),
    Product(
        id="prod_002",
        name="Cotton T-Shirt",
        description="Comfortable cotton t-shirt in various colors",
        price=24.99,
        category=ProductCategory.CLOTHING,
        stock=100,
        image_url="https://example.com/tshirt.jpg"
    ),
    Product(
        id="prod_003",
        name="Programming Book",
        description="Comprehensive guide to modern programming",
        price=49.99,
        category=ProductCategory.BOOKS,
        stock=25,
        image_url="https://example.com/book.jpg"
    ),
    Product(
        id="prod_004",
        name="Coffee Maker",
        description="Automatic coffee maker with timer",
        price=89.99,
        category=ProductCategory.HOME,
        stock=30,
        image_url="https://example.com/coffee-maker.jpg"
    ),
    Product(
        id="prod_005",
        name="Yoga Mat",
        description="Non-slip yoga mat for home workouts",
        price=34.99,
        category=ProductCategory.SPORTS,
        stock=75,
        image_url="https://example.com/yoga-mat.jpg"
    )
]
