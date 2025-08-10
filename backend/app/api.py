from fastapi import APIRouter, HTTPException
from .models import (
    Cart, CheckoutRequest, CheckoutResponse,
    AddToCartRequest, AdminReport
)
from .services import ecommerce_service

# Create router
router = APIRouter()





@router.post("/cart/add", response_model=Cart, tags=["Cart"])
async def add_to_cart(request: AddToCartRequest):
    try:
        cart = ecommerce_service.add_to_cart(request.product_id, request.quantity)
        return cart
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cart", response_model=Cart, tags=["Cart"])
async def get_cart():
    return ecommerce_service.get_cart()


@router.post("/checkout", response_model=CheckoutResponse, tags=["Checkout"])
async def checkout(request: CheckoutRequest):
    try:
        response = ecommerce_service.checkout(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))





@router.post("/admin/discount/generate", tags=["Admin"])
async def generate_discount_code():
    try:
        discount_code = ecommerce_service.generate_discount_code()
        return {
            "message": "Discount code generated successfully",
            "discount_code": discount_code.code,
            "created_at": discount_code.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/analytics", response_model=AdminReport, tags=["Admin"]) 
async def get_analytics():
    return ecommerce_service.get_analytics()


@router.delete("/cart/clear", tags=["Cart"])
async def clear_cart():
    ecommerce_service.clear_cart()
    return {"message": "Cart cleared successfully"}

