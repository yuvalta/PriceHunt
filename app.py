from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, List
import json
import os
from dotenv import load_dotenv
from aliexpress_client import AliExpressClient
import base64
from io import BytesIO
from pydantic import BaseModel

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize AliExpress client
api_key = os.getenv("ALIEXPRESS_API_KEY", "")
affiliate_id = os.getenv("ALIEXPRESS_AFFILIATE_ID", "")
app_secret = os.getenv("ALIEXPRESS_APP_SECRET", "")

print(f"API Key length: {len(api_key)}")
print(f"Affiliate ID length: {len(affiliate_id)}")
print(f"App Secret length: {len(app_secret)}")

aliexpress_client = AliExpressClient(
    api_key=api_key,
    affiliate_id=affiliate_id,
    app_secret=app_secret
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        data = await request.json()
        print("Received webhook data:", data)  # Debug log
        
        if not data or 'entry' not in data:
            print("Invalid webhook data format")  # Debug log
            return JSONResponse({"error": "Invalid webhook data format"}), 400
        
        for entry in data['entry']:
            for change in entry.get('changes', []):
                if 'value' in change and 'messages' in change['value']:
                    for message in change['value']['messages']:
                        if 'text' in message and 'body' in message['text']:
                            url = message['text']['body']
                            print(f"Processing URL: {url}")  # Debug log
                            
                            try:
                                # Extract product ID
                                product_id = aliexpress_client.extract_product_id_from_url(url)
                                if not product_id:
                                    print("Could not extract product ID from URL")  # Debug log
                                    return JSONResponse({"error": "Invalid AliExpress URL"}), 400
                                
                                print(f"Extracted product ID: {product_id}")  # Debug log
                                # Get product details
                                product = aliexpress_client.get_product_details(product_id)
                                if not product:
                                    print("Failed to get product details")  # Debug log
                                    return JSONResponse({"error": "Failed to get product details"}), 500
                                
                                print(f"Got product details: {product}")  # Debug log
                                
                                # Search for similar products
                                # todo - smartmatch_products from here with keywords
                                similar_products = aliexpress_client.search_similar_products(product_id, float(product['price']))
                                print(f"Found {len(similar_products)} similar products")  # Debug log
                                
                                return JSONResponse({
                                    "product": product,
                                    "similar_products": similar_products
                                })
                            except Exception as e:
                                print(f"Error processing product: {str(e)}")  # Debug log
                                return JSONResponse({"error": str(e)}), 500
        
        return JSONResponse({"error": "No valid message found"}), 400
    except Exception as e:
        print(f"Webhook error: {str(e)}")  # Debug log
        return JSONResponse({"error": str(e)}), 500


class ImageSearchRequest(BaseModel):
    image_base64: str
    max_price: float = None

@app.post("/search-by-image")
async def search_by_image(request: ImageSearchRequest):
    image_base64 = request.image_base64
    max_price = request.max_price

    """Search for products using an uploaded image"""
    try:
        # Search for products using the image
        results = aliexpress_client.search_by_image(image_base64, max_price)
        
        if not results:
            return JSONResponse({
                "status": "success",
                "message": "No products found matching your image.",
                "products": []
            })
        
        # Format response
        response_text = "Found products matching your image:\n\n"
        for product in results[:5]:  # Show top 5 results
            response_text += (
                f"Product: {product['title']}\n"
                f"Price: ${product['price']}\n"
                f"Link: {product['affiliate_url']}\n\n"
            )
        
        return JSONResponse({
            "status": "success",
            "message": response_text,
            "products": results
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": f"Error processing image search: {str(e)}"
        })

    # todo- add api for smartmatch_products
    



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5001,
        reload=True  # Enable hot reload
    ) 