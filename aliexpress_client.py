from typing import Dict, List, Optional
import re
from urllib.parse import urlparse, parse_qs
import time
import os
import ipdb
from iop.base import IopClient, IopRequest

class AliExpressClient:
    def __init__(self, api_key: str, affiliate_id: str, app_secret: str = None):
        if not api_key:
            raise ValueError("API Key is required for API authentication")
        if not affiliate_id:
            raise ValueError("Affiliate ID is required for API authentication")
        
        self.api_key = api_key
        self.affiliate_id = affiliate_id
        self.app_secret = app_secret or os.getenv("ALIEXPRESS_APP_SECRET", "")
        if not self.app_secret:
            raise ValueError("App Secret is required for API authentication")
        
        # Initialize the SDK client
        self.client = IopClient(
            server_url="https://api-sg.aliexpress.com/sync",
            app_key=self.api_key,
            app_secret=self.app_secret
        )
    
    def extract_product_id_from_url(self, url: str) -> Optional[str]:
        """Extract product ID from AliExpress URL"""
        try:
            # Parse the URL
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')
            
            # Look for product ID in the URL
            for part in path_parts:
                if part.startswith('item-') or part.startswith('product-'):
                    return part.split('-')[1]

                # Handle URLs ending in .html
                if part.endswith('.html'):
                    # Remove .html extension
                    part = part[:-5]
                    if part.isdigit() and len(part) > 8:
                        return part
                # Handle direct item numbers
                if part.isdigit() and len(part) > 8:
                    return part
            
            # Try to find product ID in query parameters
            query_params = parse_qs(parsed_url.query)
            if 'productId' in query_params:
                return query_params['productId'][0]
            
            return None
        except Exception:
            return None
    
    def get_product_details(self, product_id: str) -> Optional[Dict]:
        """Get product details from AliExpress API"""
        try:
            # Create request
            request = IopRequest('aliexpress.affiliate.productdetail.get')
            request.add_api_param('fields', 'product_id,product_title,product_price,product_url,commission_rate,sale_price')
            request.add_api_param('product_ids', product_id)
            request.add_api_param('target_currency', 'USD')
            request.add_api_param('target_language', 'EN')
            request.add_api_param('tracking_id', self.affiliate_id) 
            request.add_api_param('country', 'US')
                
            # Execute request
            response = self.client.execute(request)
            
            # Debug response
            print("Response body:", response.body)
            
            # Handle response
            if 'aliexpress_affiliate_productdetail_get_response' in response.body:
                product = response.body.get('aliexpress_affiliate_productdetail_get_response', '').get('resp_result', '').get('result', '').get('products', {}).get('product')[0]
            else:
                product = response.body.get('product', {})
            
            if not product :
                print("No product data found in response")
                return None
            
            return {
                "id": product.get('product_id'),
                "title": product.get('product_title'),
                "price": float(product.get('sale_price', 0)),
                "url": product.get('product_url'),
                "commission_rate": product.get('commission_rate', 0),
                "affiliate_url": self.generate_affiliate_link(product.get('product_detail_url'))
            }
        except Exception as e:
            print(f"Error getting product details: {str(e)}")
            return None
    
    def search_similar_products(self, product_id: str, max_price: float) -> List[Dict]:
        """Search for similar products with lower prices"""
        # First get the product details to get its category
        product = self.get_product_details(product_id)
        if not product:
            return []
        
        ipdb.set_trace()
        try:
            # Create request
            request = IopRequest('aliexpress.products.search')
            request.add_api_param('keywords', product['title'])
            request.add_api_param('price_range', f"0-{max_price}")
            request.add_api_param('sort', 'price_asc')
            request.add_api_param('page_size', 20)
            request.add_api_param('page_no', 1)
            
            # Execute request
            response = self.client.execute(request)
            
            if response.code != "0":
                raise Exception(response.message)
            
            products = response.body['aliexpress_products_search_response']['products']['product']
            
            # Filter and format results
            similar_products = []
            for p in products:
                if float(p['product_price']) < max_price:
                    similar_products.append({
                        "id": p['product_id'],
                        "title": p['product_title'],
                        "price": float(p['product_price']),
                        "url": p['product_url'],
                        "affiliate_url": f"{p['product_url']}?affiliate_id={self.affiliate_id}"
                    })
            
            return similar_products
        except Exception as e:
            print(f"Error searching similar products: {str(e)}")
            return []

    def search_by_image(self, image_base64: str, max_price: float = None) -> List[Dict]:
        """Search for products using an image"""
        try:
            # Create request
            request = IopRequest('aliexpress.ds.image.searchV2')
            request.add_api_param('image_base64', image_base64)
            request.add_api_param('page_size', 20)
            request.add_api_param('page_no', 1)
            
            if max_price:
                request.add_api_param('price_range', f"0-{max_price}")
            
            import ipdb
            ipdb.set_trace()
            # Execute request
            response = self.client.execute(request)
            
            if response.code != "0":
                raise Exception(response.message)
            
            products = response.body['aliexpress_ds_image_search_v2_response']['products']['product']
            
            # Format results
            search_results = []
            for p in products:
                product_data = {
                    "id": p['product_id'],
                    "title": p['product_title'],
                    "price": float(p['product_price']),
                    "url": p['product_url'],
                    "affiliate_url": f"{p['product_url']}?affiliate_id={self.affiliate_id}",
                    "image_url": p.get('product_image_url', '')
                }
                search_results.append(product_data)
            
            return search_results
        except Exception as e:
            print(f"Error searching by image: {str(e)}")
            return [] 
        
    def generate_affiliate_link(self, product_url: str) -> Optional[str]:
        """Generate an affiliate link for a product by using aliexpress.affiliate.link.generate api"""
        client = iop.IopClient(url, appkey ,appSecret)
        request = iop.IopRequest('aliexpress.affiliate.link.generate')
        request.add_api_param('source_values', product_url)
        request.add_api_param('tracking_id', self.affiliate_id)
        response = client.execute(request)
        print(response.type)
        print(response.body)

    def smartmatch_products(self, keywords: str, category_id: int = None, price_range: str = None, page_no: int = 1, page_size: int = 20, sort: str = 'price_asc') -> dict:
        """Calls the smartmatch API to get recommended products based on the provided keywords."""
        url = "https://api.aliexpress.com/affiliate/product/smartmatch"
        timestamp = int(time.time() * 1000)

        params = {
            "app_key": self.api_key,
            "session": self.access_token,
            "security_token": self.security_token,  # Include security token
            "keywords": keywords,
            "page_no": page_no,
            "page_size": page_size,
            "sort": sort,
            "category_id": category_id if category_id else "",
            "price_range": price_range if price_range else "",
            "timestamp": timestamp
        }
        sign = self.generate_signature(params)
        params["sign"] = sign
        
        response = requests.post(url, data=params)
        return response.json()
        