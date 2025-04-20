from twilio.rest import Client
import os
import json
from dotenv import load_dotenv

load_dotenv()

twilio_sid = os.getenv("TWILIO_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_whatsapp = os.getenv("FROM_WHATSAPP")

client = Client(twilio_sid, twilio_auth_token)

def send_template_message(to_number, product_title_1, product_title_2, product_title_3, product_url_1, product_url_2, product_url_3, product_price_1, product_price_2, product_price_3):
    message = client.messages.create(
        from_=from_whatsapp,
        to=to_number,
        content_sid="HXbf39d60a153dbe08c07aa1b27ccd4b95",
        content_variables=json.dumps({
            "1": product_title_1,
            "2": product_url_1,
            "3": product_price_1,
            "4": product_title_2,
            "5": product_url_2,
            "6": product_price_2,
            "7": product_title_3,
            "8": product_url_3,
            "9": product_price_3,
        })
    )
    return message.sid