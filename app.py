from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import time
from dotenv import load_dotenv
from aliexpress_client import AliExpressClient
import twilio_client
import json
from fastapi.responses import PlainTextResponse
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
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

@app.post("/")
async def root():
    logger.info("Received POST request at root")

@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming WhatsApp messages from Twilio"""
    start = time.time()
    logger.info("Received Twilio webhook request %s", request)
    try:
        form_data = await request.form()
        logger.info(f"Received Twilio webhook form data: {form_data}")

        body = form_data.get("Body")
        from_number = form_data.get("From")

        if not body or not from_number:
            # Check if this is a fallback error payload
            payload_raw = form_data.get("Payload")
            if payload_raw:
                try:
                    payload = json.loads(payload_raw)
                    params = payload.get("webhook", {}).get("request", {}).get("parameters", {})
                    body = params.get("Body")
                    from_number = params.get("From")
                except Exception as e:
                    logger.exception("Failed to parse fallback Payload")

        if not body or not from_number:
            logger.warning("Missing 'Body' or 'From' in all sources")
            twilio_client.send_generic_error_message(from_number)
            return JSONResponse({"error": "Invalid Twilio webhook data"}, status_code=400)

        logger.info(f"Incoming message from {from_number}: {body}")

        if body == 'start':
            twilio_client.send_instruction_message(from_number)
            return JSONResponse({"message": "Instructions sent"}, status_code=200)
        
        url = body

        # Check if the message is a valid URL
        if not is_valid_url(url):
            logger.warning("Invalid URL format")
            twilio_client.send_input_error_message(from_number)
            return JSONResponse({"error": "Invalid URL format"}, status_code=400)

        twilio_client.send_thinking_message(from_number)

        try:
            product_id = aliexpress_client.extract_product_id_from_url(url)
            if not product_id:
                logger.warning("Could not extract product ID from URL")
                logger.info("Trying to expand shortlink")
                expanded_url = await aliexpress_client.expand_shortlink(url)
                if expanded_url:
                    logger.info(f"Expanded URL: {expanded_url}")
                    product_id = aliexpress_client.extract_product_id_from_url(expanded_url)
                    if not product_id:
                        logger.warning("Could not extract product ID from expanded URL")
                        twilio_client.send_input_error_message(from_number)
                        return JSONResponse({"error": "Invalid AliExpress URL"}, status_code=400)
                else:
                    logger.error("Failed to expand shortlink")
                    twilio_client.send_input_error_message(from_number)
                    return JSONResponse({"error": "Invalid AliExpress URL"}, status_code=400)

            product = aliexpress_client.get_single_product_details(product_id)
            if not product:
                logger.error("Failed to get product details")
                twilio_client.send_cant_find_product(from_number)
                return JSONResponse({"error": "Failed to get product details"}, status_code=500)

            similar_products_with_affiliate = aliexpress_client.similar_products(product)

            end = time.time()

            twilio_client.send_template_message(
                to_number=from_number,
                product_title_1=similar_products_with_affiliate[0]["title"],
                product_title_2=similar_products_with_affiliate[1]["title"],
                product_title_3=similar_products_with_affiliate[2]["title"],
                product_url_1=similar_products_with_affiliate[0]["affiliate_url"],
                product_url_2=similar_products_with_affiliate[1]["affiliate_url"],
                product_url_3=similar_products_with_affiliate[2]["affiliate_url"] ,
                product_price_1=similar_products_with_affiliate[0]["price"],
                product_price_2=similar_products_with_affiliate[1]["price"],
                product_price_3=similar_products_with_affiliate[2]["price"]
            )

            logging.info({
                "took": end - start,
                "original_product": {product["product_title"]: product["target_sale_price"]},
                "cheaper_products": [{p["affiliate_url"]: p["price"]} for p in similar_products_with_affiliate],
            })

            return PlainTextResponse("OK", status_code=200)

        except Exception as e:
            logger.exception(f"Error processing product: {e}")
            twilio_client.send_generic_error_message(from_number)
            return JSONResponse({"error": str(e)}, status_code=500)

    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
    
def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])
    
if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)
