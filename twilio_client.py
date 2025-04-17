from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

twilio_sid = os.getenv("TWILIO_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_whatsapp = os.getenv("FROM_WHATSAPP")

client = Client(twilio_sid, twilio_auth_token)

def send_template_message(to_number, product_title, cheaper_links):
    cheaper_text = "\n".join([f"- {p_url} (${p_price})" for p_url, p_price in cheaper_links])

    message = client.messages.create(
        from_=from_whatsapp,
        to=to_number,
        content_sid="your_template_sid",  # Only for content templates created in Twilio's Content API
        content_variables={
            "1": product_title,
            "2": cheaper_text
        }
    )
    return message.sid