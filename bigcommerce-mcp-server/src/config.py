"""Configuration for the BigCommerce MCP Server"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Config:
    """Configuration for the BigCommerce MCP Server"""
    
    # Paths
    docs_path: Optional[Path] = None
    cache_path: Optional[Path] = None
    
    # Search configuration
    max_search_results: int = 50
    enable_semantic_search: bool = True
    
    # Indexing configuration
    rebuild_indexes_on_startup: bool = False
    index_cache_ttl: int = 3600  # 1 hour
    
    # API configuration
    supported_api_versions: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.docs_path is None:
            self.docs_path = Path.cwd()
        
        if self.cache_path is None:
            self.cache_path = self.docs_path / ".cache"
        
        if self.supported_api_versions is None:
            self.supported_api_versions = ["v2", "v3"]
        
        # Ensure cache directory exists
        self.cache_path.mkdir(exist_ok=True) 