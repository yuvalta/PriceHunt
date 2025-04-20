from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs
import os
from iop.base import IopClient, IopRequest
import logging
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

class AliExpressClient:
    def __init__(self, api_key: str, affiliate_id: str, app_secret: Optional[str] = None):
        if not api_key:
            raise ValueError("API Key is required")
        if not affiliate_id:
            raise ValueError("Affiliate ID is required")
        
        self.api_key = api_key
        self.affiliate_id = affiliate_id
        self.app_secret = app_secret or os.getenv("ALIEXPRESS_APP_SECRET")
        if not self.app_secret:
            raise ValueError("App Secret is required")
        
        self.client = IopClient(
            server_url="https://api-sg.aliexpress.com/sync",
            app_key=self.api_key,
            app_secret=self.app_secret
        )

    def extract_product_id_from_url(self, url: str) -> Optional[str]:
        try:
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')
            for part in path_parts:
                if part.startswith(('item-', 'product-')):
                    return part.split('-')[1]
                if part.endswith('.html'):
                    part = part[:-5]
                if part.isdigit() and len(part) > 8:
                    return part
            query_params = parse_qs(parsed_url.query)
            return query_params.get('productId', [None])[0]
        except Exception as e:
            logging.error(f"Failed to extract product ID: {e}")
            return None


    async def expand_shortlink(url):
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                response = await client.head(url)
                return str(response.url)
        except Exception as e:
            print(f"Error expanding shortlink: {e}")
            return None
        

    def _fetch_product_details(self, product_ids: str) -> Optional[List[Dict]]:
        try:
            request = IopRequest('aliexpress.affiliate.productdetail.get')
            request.add_api_param('fields', 'product_id,product_title,product_price,product_url,commission_rate,sale_price,product_detail_url')
            request.add_api_param('product_ids', product_ids)
            request.add_api_param('target_currency', 'USD')
            request.add_api_param('target_language', 'EN')
            request.add_api_param('tracking_id', self.affiliate_id)
            request.add_api_param('country', 'US')

            response = self.client.execute(request)
            products = response.body.get('aliexpress_affiliate_productdetail_get_response', {}) \
                                   .get('resp_result', {}) \
                                   .get('result', {}) \
                                   .get('products', {}) \
                                   .get('product', [])

            logging.info(f"Response from product details API: {response.body}")
            
            if not products:
                logging.warning("No product data found in response")
                return None

            logging.info(f"Fetched product details: {products}")
            return products

        except Exception as e:
            logging.exception(f"Error fetching product details: {e}")
            return None

    def get_single_product_details(self, product_id: str) -> Optional[Dict]:
        logging.info(f"Fetching details for product ID: {product_id}")
        results = self._fetch_product_details(product_id)
        return results[0] if results else None

    def generate_affiliate_link(self, product_url: str) -> Optional[str]:
        try:
            request = IopRequest('aliexpress.affiliate.link.generate')
            request.add_api_param('source_values', product_url)
            request.add_api_param("promotion_link_type", 2);
            request.add_api_param('tracking_id', self.affiliate_id)
            response = self.client.execute(request)

            links = response.body.get('aliexpress_affiliate_link_generate_response', {}) \
                                 .get('resp_result', {}) \
                                 .get('result', {}) \
                                 .get('promotion_links', [])
            
            logging.info(f"Generated affiliate links: {links}")

            return links.get('promotion_link') if links else None
        except Exception as e:
            logging.exception(f"Error generating affiliate link: {e}")
            return None

    def similar_products(self, product: Dict) -> Optional[str]:
        try:
            request = IopRequest('aliexpress.affiliate.product.query')
            request.add_api_param('keywords', product["product_title"])
            request.add_api_param('sort', 'SALE_PRICE_ASC')
            request.add_api_param('page_no', 1)
            request.add_api_param('page_size', 10)
            request.add_api_param('target_currency', 'USD')
            request.add_api_param('target_language', 'EN')

            logging.info(f"Requesting similar products for: {product['product_title']}")

            response = self.client.execute(request)
            products = response.body.get('aliexpress_affiliate_product_query_response', {}) \
                                   .get('resp_result', {}) \
                                   .get('result', {}) \
                                   .get('products', {}) \
                                   .get('product', [])

            if not products:
                logging.warning("No similar products found")
                return None
            
            logging.info(f"Response from similar products API: {response.body}")

            cheaper_products = [p for p in products if p.get('product_id') and float(p.get('target_sale_price')) < float(product.get('target_sale_price'))]
            sort_cheaper_products = sorted(cheaper_products, key=lambda x: float(x.get('target_sale_price', 0)))[:min(3, len(cheaper_products))]

            logging.info(f"Cheaper products found: {sort_cheaper_products}")

            results = []
            for p in sort_cheaper_products:
                affiliate_link = self.generate_affiliate_link(p.get('product_detail_url'))[0]
                logging.info(f"Generated affiliate link: {affiliate_link.get('promotion_link')}")
                results.append({
                    "id": p.get('product_id'),
                    "title": p.get('product_title'),
                    "price": float(p.get('target_sale_price', 0)),
                    "url": p.get('product_detail_url'),
                    "commission_rate": p.get('commission_rate', 0),
                    "affiliate_url": affiliate_link.get('promotion_link'),
                })


            return results
        except Exception as e:
            logging.exception(f"similar failed: {e}")
            return None
