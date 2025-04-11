from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import time
from dotenv import load_dotenv
from aliexpress_client import AliExpressClient

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

logger.info(f"API Key length: {len(api_key)}")
logger.info(f"Affiliate ID length: {len(affiliate_id)}")
logger.info(f"App Secret length: {len(app_secret)}")

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
    start = time.time()
    try:
        data = await request.json()
        logger.debug(f"Received webhook data: {data}")

        if not data or 'entry' not in data:
            logger.warning("Invalid webhook data format")
            return JSONResponse({"error": "Invalid webhook data format"}, status_code=400)

        for entry in data['entry']:
            for change in entry.get('changes', []):
                if 'value' in change and 'messages' in change['value']:
                    for message in change['value']['messages']:
                        text_body = message.get("text", {}).get("body")
                        if text_body:
                            url = text_body
                            logger.info(f"Processing URL: {url}")

                            try:
                                product_id = aliexpress_client.extract_product_id_from_url(url)
                                if not product_id:
                                    logger.warning("Could not extract product ID from URL")
                                    return JSONResponse({"error": "Invalid AliExpress URL"}, status_code=400)

                                product = aliexpress_client.get_single_product_details(product_id)
                                if not product:
                                    logger.error("Failed to get product details")
                                    return JSONResponse({"error": "Failed to get product details"}, status_code=500)

                                # TODO: Use real matching logic instead of dummy smartmatch
                                similar_products_ids = aliexpress_client.smartmatch_products(product)
                                logger.info(f"Smartmatched product IDs: {similar_products_ids}")

                                product_similar_by_id = aliexpress_client.get_multiple_products_details(similar_products_ids)

                                if not product_similar_by_id:
                                    logger.error("No similar products found")
                                    return JSONResponse({"error": "No similar products found"}, status_code=404)

                                cheaper_products = [
                                    p for p in product_similar_by_id if p["price"] < product["price"]
                                ]

                                end = time.time()

                                return JSONResponse({
                                    "took": end - start,
                                    "original_product": {product["title"]: product["price"]},
                                    "cheaper_products": [{p["affiliate_url"]: p["price"]} for p in cheaper_products],
                                })

                            except Exception as e:
                                logger.exception(f"Error processing product: {e}")
                                return JSONResponse({"error": str(e)}, status_code=500)

        return JSONResponse({"error": "No valid message found"}, status_code=400)

    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)
