from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class BaseService(ABC):
    """Base class for all services"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    @abstractmethod
    async def initialize(self):
        """Initialize the service"""
        pass
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        return self._cache.get(key)
    
    def set_cached(self, key: str, value: Any):
        """Set value in cache"""
        self._cache[key] = value
    
    def clear_cache(self):
        """Clear the cache"""
        self._cache.clear()

class BaseModelWithCache(BaseModel):
    """Base model with caching capabilities"""
    
    class Config:
        arbitrary_types_allowed = True
    
    def cache_key(self) -> str:
        """Generate a cache key for this model"""
        return f"{self.__class__.__name__}:{id(self)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModelWithCache':
        """Create model from dictionary"""
        return cls(**data) 