from typing import Dict, List, Optional
import re
from urllib.parse import urlparse, parse_qs
import requests
import time
import hashlib
import hmac
import base64

class AliExpressClient:
    def __init__(self, api_key: str, affiliate_id: str):
        self.api_key = api_key
        self.affiliate_id = affiliate_id
        self.base_url = "https://api.aliexpress.com/v2"
        self.app_secret = ""  # You'll need to add your app secret here
    
    def _generate_signature(self, params: Dict) -> str:
        """Generate signature for API request"""
        # Sort parameters alphabetically
        sorted_params = sorted(params.items())
        
        # Create string to sign
        string_to_sign = self.app_secret
        for key, value in sorted_params:
            string_to_sign += key + value
        string_to_sign += self.app_secret
        
        # Generate signature
        signature = hmac.new(
            self.app_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    def _make_request(self, method: str, params: Dict) -> Dict:
        """Make API request to AliExpress"""
        # Add common parameters
        params.update({
            'app_key': self.api_key,
            'method': method,
            'timestamp': str(int(time.time() * 1000)),
            'format': 'json',
            'v': '2.0',
            'sign_method': 'hmac'
        })
        
        # Generate signature
        params['sign'] = self._generate_signature(params)
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
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
            
            # Try to find product ID in query parameters
            query_params = parse_qs(parsed_url.query)
            if 'productId' in query_params:
                return query_params['productId'][0]
            
            return None
        except Exception:
            return None
    
    def get_product_details(self, product_id: str) -> Optional[Dict]:
        """Get product details from AliExpress API"""
        params = {
            'product_id': product_id,
            'fields': 'product_id,product_title,product_price,product_url'
        }
        
        try:
            response = self._make_request('aliexpress.product.details.get', params)
            
            if 'error_response' in response:
                raise Exception(response['error_response']['msg'])
            
            product = response['aliexpress_product_details_get_response']['product']
            
            return {
                "id": product['product_id'],
                "title": product['product_title'],
                "price": float(product['product_price']),
                "url": product['product_url'],
                "affiliate_url": f"{product['product_url']}?affiliate_id={self.affiliate_id}"
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
        
        # Search for similar products
        params = {
            'keywords': product['title'],
            'price_range': f"0-{max_price}",
            'sort': 'price_asc',
            'page_size': 20,
            'page_no': 1
        }
        
        try:
            response = self._make_request('aliexpress.products.search', params)
            
            if 'error_response' in response:
                raise Exception(response['error_response']['msg'])
            
            products = response['aliexpress_products_search_response']['products']['product']
            
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