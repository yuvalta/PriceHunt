import logging
import os
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

class AliExpressClient:
    BASE_URL = "https://api-sg.aliexpress.com/sync"

    def __init__(self, api_key: str, affiliate_id: str, app_secret: Optional[str] = None):
        if not api_key or not affiliate_id:
            raise ValueError("API Key and Affiliate ID are required")
        self.api_key = api_key
        self.affiliate_id = affiliate_id
        self.app_secret = app_secret or os.getenv("ALIEXPRESS_APP_SECRET")
        if not self.app_secret:
            raise ValueError("App Secret is required")

    def extract_product_id_from_url(self, url: str) -> Optional[str]:
        try:
            parsed_url = urlparse(url)
            for part in parsed_url.path.split('/'):
                if part.startswith(('item-', 'product-')):
                    return part.split('-')[1]
                if part.endswith('.html'):
                    part = part[:-5]
                if part.isdigit() and len(part) > 8:
                    return part
            return parse_qs(parsed_url.query).get('productId', [None])[0]
        except Exception as e:
            logging.error(f"Failed to extract product ID: {e}")
            return None

    async def _post(self, method: str, params: Dict) -> Optional[Dict]:
        full_params = {
            "app_key": self.api_key,
            "method": method,
            "sign_method": "hmac",
            "timestamp": "2025-01-01 00:00:00",  # Update to current time or use a signature utility
            "v": "1.0",
            **params
        }

        # TODO: Sign request with HMAC and add 'sign' key here
        # full_params["sign"] = your_signature_function(full_params, self.app_secret)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.BASE_URL, data=full_params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logging.exception(f"HTTP request failed: {e}")
                return None

    async def get_single_product_details(self, product_id: str) -> Optional[Dict]:
        result = await self._fetch_product_details(product_id)
        return result[0] if result else None

    async def get_multiple_products_details(self, product_ids: str) -> Optional[List[Dict]]:
        return await self._fetch_product_details(product_ids)

    async def _fetch_product_details(self, product_ids: str) -> Optional[List[Dict]]:
        data = await self._post("aliexpress.affiliate.productdetail.get", {
            "fields": "product_id,product_title,product_price,product_url,commission_rate,sale_price,product_detail_url",
            "product_ids": product_ids,
            "target_currency": "USD",
            "target_language": "EN",
            "tracking_id": self.affiliate_id,
            "country": "US"
        })
        try:
            products = data['aliexpress_affiliate_productdetail_get_response']['resp_result']['result']['products']['product']
            result = []
            for p in products:
                affiliate_link = await self.generate_affiliate_link(p['product_detail_url'])
                result.append({
                    "id": p["product_id"],
                    "title": p["product_title"],
                    "price": float(p["target_sale_price"]),
                    "url": p["product_detail_url"],
                    "commission_rate": p["commission_rate"],
                    "affiliate_url": affiliate_link,
                })
            return result
        except Exception as e:
            logging.exception(f"Error parsing product details: {e}")
            return None

    async def generate_affiliate_link(self, product_url: str) -> Optional[str]:
        data = await self._post("aliexpress.affiliate.link.generate", {
            "source_values": product_url,
            "promotion_link_type": 2,
            "tracking_id": self.affiliate_id
        })
        try:
            links = data['aliexpress_affiliate_link_generate_response']['resp_result']['result']['promotion_links']
            return links[0]['promotion_link'] if links else None
        except Exception as e:
            logging.exception(f"Error parsing affiliate link: {e}")
            return None

    async def smartmatch_products(self, product: Dict) -> Optional[str]:
        data = await self._post("aliexpress.affiliate.product.smartmatch", {
            "keywords": product["title"],
            "product_id": product["id"],
            "page_no": 1,
            "device_id": "aaaaaa"
        })
        try:
            products = data['aliexpress_affiliate_product_smartmatch_response']['resp_result']['result']['products']['product']
            cheaper = sorted(
                [p for p in products if float(p['target_sale_price']) < product['price']],
                key=lambda x: float(x['target_sale_price'])
            )[:3]
            return ",".join(p['product_id'] for p in cheaper)
        except Exception as e:
            logging.exception(f"Smartmatch parsing failed: {e}")
            return None
