from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from ..services.aliexpress import AliExpressService
from ..models.product import Product
from typing import List

router = APIRouter()
aliexpress_service = AliExpressService()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@router.post("/webhook")
async def webhook(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        body = await request.json()
        
        # Extract message from WhatsApp webhook
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        message = value.get("messages", [{}])[0]
        
        if not message:
            return JSONResponse({"status": "ok"})
        
        # Get the message text
        text = message.get("text", {}).get("body", "")
        
        # Handle direct AliExpress product link
        if "aliexpress.com" in text.lower():
            product_id = aliexpress_service.extract_product_id_from_url(text)
            if not product_id:
                return JSONResponse({
                    "status": "error",
                    "message": "Could not extract product ID from the URL"
                })
            
            # Get product details
            product = aliexpress_service.get_product_details(product_id)
            if not product:
                return JSONResponse({
                    "status": "error",
                    "message": "Product not found"
                })
            
            # Search for cheaper alternatives
            similar_products = aliexpress_service.search_similar_products(product_id, product.price)
            
            if similar_products:
                # Find the cheapest alternative
                cheapest_alternative = min(similar_products, key=lambda x: x.price)
                response_text = (
                    f"Found a cheaper alternative for {product.title}!\n"
                    f"Original price: ${product.price}\n"
                    f"Alternative: {cheapest_alternative.title}\n"
                    f"Price: ${cheapest_alternative.price}\n"
                    f"Link: {cheapest_alternative.affiliate_url}"
                )
            else:
                response_text = (
                    f"Product: {product.title}\n"
                    f"Price: ${product.price}\n"
                    f"Sorry, couldn't find a cheaper alternative."
                )
            
            return JSONResponse({
                "status": "success",
                "message": response_text
            })
        
        # Handle search command
        if text.startswith("/search"):
            # Format: /search keywords price
            parts = text.split()
            if len(parts) != 3:
                return JSONResponse({
                    "status": "error",
                    "message": "Please use format: /search keywords price"
                })
            
            keywords = parts[1]
            try:
                max_price = float(parts[2])
            except ValueError:
                return JSONResponse({
                    "status": "error",
                    "message": "Please provide a valid price"
                })
            
            # Search for products
            params = {
                'keywords': keywords,
                'price_range': f"0-{max_price}",
                'sort': 'price_asc',
                'page_size': 20,
                'page_no': 1
            }
            
            try:
                response = aliexpress_service._make_request('aliexpress.products.search', params)
                
                if 'error_response' in response:
                    return JSONResponse({
                        "status": "error",
                        "message": response['error_response']['msg']
                    })
                
                products_data = response['aliexpress_products_search_response']['products']['product']
                
                if not products_data:
                    return JSONResponse({
                        "status": "success",
                        "message": "No products found matching your criteria."
                    })
                
                # Get the cheapest product
                cheapest_product = min(products_data, key=lambda x: float(x['product_price']))
                
                response_text = (
                    f"Found a product matching your criteria!\n"
                    f"Product: {cheapest_product['product_title']}\n"
                    f"Price: ${float(cheapest_product['product_price'])}\n"
                    f"Link: {cheapest_product['product_url']}?affiliate_id={aliexpress_service.affiliate_id}"
                )
                
                return JSONResponse({
                    "status": "success",
                    "message": response_text
                })
                
            except Exception as e:
                return JSONResponse({
                    "status": "error",
                    "message": f"Error searching products: {str(e)}"
                })
        
        return JSONResponse({"status": "ok"})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 