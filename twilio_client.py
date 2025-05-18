from twilio.rest import Client
import os
from dotenv import load_dotenv
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

twilio_sid = os.getenv("TWILIO_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_whatsapp = os.getenv("FROM_WHATSAPP")
ADMIN_WHATSAPP = os.getenv("ADMIN_WHATSAPP")

client = Client(twilio_sid, twilio_auth_token)

def send_template_message(to_number, product_title_1, product_title_2, product_title_3,
                          product_url_1, product_url_2, product_url_3,
                          product_price_1, product_price_2, product_price_3):
    
    content_variables = json.dumps({
        "1": product_title_1,
        "2": str(product_price_1),
        "3": product_url_1,
        "4": product_title_2,
        "5": str(product_price_2),
        "6": product_url_2,
        "7": product_title_3,
        "8": str(product_price_3),
        "9": product_url_3,
    })

    logger.info(f"Sending message to {to_number} with content variables: {content_variables}")

    message = client.messages.create(
        from_=from_whatsapp,
        to=to_number,
        content_sid="HXca4fbd21c71303d99c99a6fecc097647",
        content_variables=content_variables
    )
    
    return message.sid

def send_thinking_message(to_number):
    message = client.messages.create(
        from_=from_whatsapp,
        to=to_number,
        body="Thinking... 💭"
    )
    
    return message.sid

def send_generic_error_message(to_number):
    message = client.messages.create(
        from_=from_whatsapp,
        to=to_number,
        body="Oops! ❌"
    )
    
    return message.sid

def send_input_error_message(to_number):
    message = client.messages.create(
        from_=from_whatsapp,
        to=to_number,
        body="""
            Oops! ❌ 
            I didn't understand that. 
            Please send a valid product link 👌

            The best link to search look like this ✅
            https://www.aliexpress.com/item/1234567890.html
            """
    )
    
    return message.sid

def send_cant_find_product_message(to_number):
    message = client.messages.create(
        from_=from_whatsapp,
        to=to_number,
        body="I couldn't find the product you were looking for. Please try again with a different link."
    )
    
    return message.sid

def send_instruction_message(to_number):
    message = client.messages.create(
        from_=from_whatsapp,
        to=to_number,
        body="""
            Hi! 👋 I'm Price Hunt
            Just send me your Aliexpress product link and I'll find 3 cheaper products for you
            """
    )
    
    return message.sid

def send_cant_find_product(to_number):
    message = client.messages.create(
        from_=from_whatsapp,
        to=to_number,
        body="I couldn't find the product you were looking for. Probabaly yours is the cheapest."
    )
    
    return message.sid

def send_user_messaged_bot(user_number, message):
    if user_number != ADMIN_WHATSAPP:
        message = client.messages.create(
        from_=from_whatsapp,
        to=ADMIN_WHATSAPP,
        body="Phone number: " + user_number + " messaged the bot with the following message: " + message
        )
        return message.sid
    return 