from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import time
import asyncio
from dotenv import load_dotenv
from aliexpress_client import AliExpressClient
import twilio_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000", "http://127.0.0.1:8000",
        "http://localhost:8080", "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AliExpress client
api_key = os.getenv("ALIEXPRESS_API_KEY", "")
affiliate_id = os.getenv("ALIEXPRESS_AFFILIATE_ID", "")
app_secret = os.getenv("ALIEXPRESS_APP_SECRET", "")

aliexpress_client = AliExpressClient(
    api_key=api_key,
    affiliate_id=affiliate_id,
    app_secret=app_secret
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhook")
async def webhook(request: Request):
    start = time.time()
    try:
        form_data = await request.form()

        body = form_data.get("Body")
        from_number = form_data.get("From")

        if not body or not from_number:
            payload = form_data.get("Payload")
            if payload:
                return JSONResponse({"debug": "twilio_payload", "payload": payload}, status_code=200)
            return JSONResponse({"error": "Invalid Twilio webhook data"}, status_code=400)

        url = body
        product_id = aliexpress_client.extract_product_id_from_url(url)
        if not product_id:
            return JSONResponse({"error": "Invalid AliExpress URL"}, status_code=400)

        # Fetch product and smartmatch data concurrently
        product_task = asyncio.to_thread(aliexpress_client.get_single_product_details, product_id)
        product = await product_task
        if not product:
            return JSONResponse({"error": "Failed to get product details"}, status_code=500)

        smartmatch_task = asyncio.to_thread(aliexpress_client.smartmatch_products, product)
        similar_ids = await smartmatch_task
        if not similar_ids:
            return JSONResponse({"error": "No smartmatched products found"}, status_code=404)

        similar_products_task = asyncio.to_thread(aliexpress_client.get_multiple_products_details, similar_ids)
        similar_products = await similar_products_task
        if not similar_products:
            return JSONResponse({"error": "No similar products found"}, status_code=404)

        cheaper_products = sorted(
            [p for p in similar_products if p["price"] < product["price"]],
            key=lambda x: x["price"]
        )[:3]

        if len(cheaper_products) < 3:
            return JSONResponse({"error": "Not enough cheaper products found"}, status_code=404)

        # Send message
        await asyncio.to_thread(
            twilio_client.send_template_message,
            to_number=from_number,
            product_title_1=cheaper_products[0]["title"],
            product_title_2=cheaper_products[1]["title"],
            product_title_3=cheaper_products[2]["title"],
            product_url_1=cheaper_products[0]["url"],
            product_url_2=cheaper_products[1]["url"],
            product_url_3=cheaper_products[2]["url"],
            product_price_1=cheaper_products[0]["price"],
            product_price_2=cheaper_products[1]["price"],
            product_price_3=cheaper_products[2]["price"]
        )

        end = time.time()

        return JSONResponse({
            "took": round(end - start, 2),
            "original_product": {product["title"]: product["price"]},
            "cheaper_products": [{p["affiliate_url"]: p["price"]} for p in cheaper_products],
        })

    except Exception as e:
        logger.exception("Error in webhook")
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)
