from typing import Dict, List, Optional
import requests
import time
import hashlib
import hmac
import base64
from urllib.parse import urlparse, parse_qs
from ..models.product import Product
from ..config.settings import get_settings

settings = get_settings()

class AliExpressService:
    def __init__(self):
        self.api_key = settings.ALIEXPRESS_API_KEY
        self.affiliate_id = settings.ALIEXPRESS_AFFILIATE_ID
        self.app_secret = settings.ALIEXPRESS_APP_SECRET
        self.base_url = "https://api.aliexpress.com/v2"
    
    def _generate_signature(self, params: Dict) -> str:
        """Generate signature for API request"""
        sorted_params = sorted(params.items())
        string_to_sign = self.app_secret
        for key, value in sorted_params:
            string_to_sign += key + value
        string_to_sign += self.app_secret
        
        signature = hmac.new(
            self.app_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    def _make_request(self, method: str, params: Dict) -> Dict:
        """Make API request to AliExpress"""
        params.update({
            'app_key': self.api_key,
            'method': method,
            'timestamp': str(int(time.time() * 1000)),
            'format': 'json',
            'v': '2.0',
            'sign_method': 'hmac'
        })
        
        params['sign'] = self._generate_signature(params)
        
        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=settings.TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def extract_product_id_from_url(self, url: str) -> Optional[str]:
        """Extract product ID from AliExpress URL"""
        try:
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')
            
            for part in path_parts:
                if part.startswith('item-') or part.startswith('product-'):
                    return part.split('-')[1]
            
            query_params = parse_qs(parsed_url.query)
            if 'productId' in query_params:
                return query_params['productId'][0]
            
            return None
        except Exception:
            return None
    
    def get_product_details(self, product_id: str) -> Optional[Product]:
        """Get product details from AliExpress API"""
        params = {
            'product_id': product_id,
            'fields': 'product_id,product_title,product_price,product_url,product_description,product_image_url,product_rating,product_reviews_count'
        }
        
        try:
            response = self._make_request('aliexpress.product.details.get', params)
            
            if 'error_response' in response:
                raise Exception(response['error_response']['msg'])
            
            product_data = response['aliexpress_product_details_get_response']['product']
            
            return Product(
                id=product_data['product_id'],
                title=product_data['product_title'],
                price=float(product_data['product_price']),
                url=product_data['product_url'],
                affiliate_url=f"{product_data['product_url']}?affiliate_id={self.affiliate_id}",
                description=product_data.get('product_description'),
                image_url=product_data.get('product_image_url'),
                rating=float(product_data.get('product_rating', 0)),
                reviews_count=int(product_data.get('product_reviews_count', 0))
            )
        except Exception as e:
            print(f"Error getting product details: {str(e)}")
            return None
    
    def search_similar_products(self, product_id: str, max_price: float) -> List[Product]:
        """Search for similar products with lower prices"""
        product = self.get_product_details(product_id)
        if not product:
            return []
        
        params = {
            'keywords': product.title,
            'price_range': f"0-{max_price}",
            'sort': 'price_asc',
            'page_size': 20,
            'page_no': 1
        }
        
        try:
            response = self._make_request('aliexpress.products.search', params)
            
            if 'error_response' in response:
                raise Exception(response['error_response']['msg'])
            
            products_data = response['aliexpress_products_search_response']['products']['product']
            
            similar_products = []
            for p in products_data:
                if float(p['product_price']) < max_price:
                    similar_products.append(Product(
                        id=p['product_id'],
                        title=p['product_title'],
                        price=float(p['product_price']),
                        url=p['product_url'],
                        affiliate_url=f"{p['product_url']}?affiliate_id={self.affiliate_id}",
                        description=p.get('product_description'),
                        image_url=p.get('product_image_url'),
                        rating=float(p.get('product_rating', 0)),
                        reviews_count=int(p.get('product_reviews_count', 0))
                    ))
            
            return similar_products
        except Exception as e:
            print(f"Error searching similar products: {str(e)}")
            return [] 