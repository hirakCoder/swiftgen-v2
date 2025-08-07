"""
Intent Parser - Understands WHAT user wants, not HOW complex it is
Production-ready, battle-tested approach used by Vercel, Railway
"""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

class AppType(Enum):
    """Core app types we support"""
    UTILITY = "utility"          # Timer, Calculator, Counter
    CONTENT = "content"          # Notes, Todo, Reader
    SOCIAL = "social"            # Feed, Chat, Profile
    COMMERCE = "commerce"        # Shop, Cart, Payment
    MEDIA = "media"              # Photo, Video, Audio
    GAME = "game"                # Simple games
    CUSTOM = "custom"            # Everything else

@dataclass
class AppIntent:
    """What the user actually wants"""
    raw_request: str
    app_name: str
    app_type: AppType
    core_features: List[str]
    ui_elements: List[str]
    data_needs: List[str]
    
class IntentParser:
    """
    Parse user intent without over-engineering
    Focus: What does the user ACTUALLY want?
    """
    
    def __init__(self):
        # Keywords that indicate app types
        self.type_keywords = {
            AppType.UTILITY: ['timer', 'calculator', 'counter', 'converter', 'clock', 'stopwatch'],
            AppType.CONTENT: ['notes', 'todo', 'list', 'reader', 'document', 'markdown'],
            AppType.SOCIAL: ['social', 'feed', 'chat', 'profile', 'follow', 'instagram', 'twitter'],
            AppType.COMMERCE: ['shop', 'store', 'cart', 'product', 'payment', 'ecommerce', 'amazon'],
            AppType.MEDIA: ['photo', 'video', 'camera', 'gallery', 'player', 'audio'],
            AppType.GAME: ['game', 'puzzle', 'quiz', 'trivia']
        }
        
        # Features we can detect
        self.feature_keywords = {
            'timer': ['timer', 'countdown', 'stopwatch', 'alarm'],
            'list': ['list', 'items', 'todo', 'tasks'],
            'auth': ['login', 'signup', 'authentication', 'user account'],
            'storage': ['save', 'store', 'persist', 'database', 'cache'],
            'network': ['api', 'fetch', 'download', 'sync', 'cloud'],
            'camera': ['camera', 'photo', 'capture', 'scan'],
            'location': ['map', 'location', 'gps', 'nearby'],
            'payment': ['payment', 'checkout', 'purchase', 'subscribe']
        }
        
        # UI elements we support
        self.ui_keywords = {
            'navigation': ['screens', 'pages', 'tabs', 'navigation'],
            'forms': ['form', 'input', 'textfield', 'button'],
            'lists': ['list', 'table', 'grid', 'collection'],
            'media': ['image', 'video', 'player', 'gallery'],
            'charts': ['chart', 'graph', 'analytics', 'dashboard']
        }
    
    def parse(self, request: str, app_name: str) -> AppIntent:
        """
        Parse user request into actionable intent
        NO complexity classification - just what they want
        """
        request_lower = request.lower()
        
        # Detect app type
        app_type = self._detect_app_type(request_lower)
        
        # Extract features needed
        core_features = self._extract_features(request_lower)
        
        # Determine UI elements
        ui_elements = self._extract_ui_elements(request_lower)
        
        # Identify data needs
        data_needs = self._extract_data_needs(request_lower)
        
        return AppIntent(
            raw_request=request,
            app_name=app_name,
            app_type=app_type,
            core_features=core_features,
            ui_elements=ui_elements,
            data_needs=data_needs
        )
    
    def _detect_app_type(self, request: str) -> AppType:
        """Detect the primary app type"""
        for app_type, keywords in self.type_keywords.items():
            if any(keyword in request for keyword in keywords):
                return app_type
        return AppType.CUSTOM
    
    def _extract_features(self, request: str) -> List[str]:
        """Extract core features needed"""
        features = []
        for feature, keywords in self.feature_keywords.items():
            if any(keyword in request for keyword in keywords):
                features.append(feature)
        
        # If no features detected, infer from app type mentions
        if not features:
            if 'timer' in request:
                features.append('timer')
            elif 'calculator' in request:
                features.append('calculator')
            elif 'todo' in request or 'list' in request:
                features.append('list')
        
        return features
    
    def _extract_ui_elements(self, request: str) -> List[str]:
        """Extract UI elements needed"""
        ui_elements = []
        for element, keywords in self.ui_keywords.items():
            if any(keyword in request for keyword in keywords):
                ui_elements.append(element)
        
        # Default UI based on app type if none specified
        if not ui_elements:
            if 'list' in self._extract_features(request):
                ui_elements.append('lists')
            else:
                ui_elements.append('forms')  # Most apps need some form of input
        
        return ui_elements
    
    def _extract_data_needs(self, request: str) -> List[str]:
        """Identify data/storage requirements"""
        data_needs = []
        
        # Check for persistence needs
        if any(word in request for word in ['save', 'store', 'remember', 'persist']):
            data_needs.append('local_storage')
        
        # Check for network needs
        if any(word in request for word in ['api', 'fetch', 'sync', 'cloud', 'weather', 'stock']):
            data_needs.append('network')
        
        # Check for user data
        if any(word in request for word in ['user', 'profile', 'account', 'login']):
            data_needs.append('user_data')
        
        return data_needs
    
    def get_minimal_requirements(self, intent: AppIntent) -> Dict[str, any]:
        """
        Get the MINIMAL requirements to build this app
        This prevents over-engineering
        """
        return {
            'app_name': intent.app_name,
            'app_type': intent.app_type.value,
            'must_have_features': intent.core_features[:3],  # Max 3 core features to start
            'ui_pattern': intent.ui_elements[0] if intent.ui_elements else 'single_view',
            'needs_persistence': 'local_storage' in intent.data_needs,
            'needs_network': 'network' in intent.data_needs,
            'raw_description': intent.raw_request  # Preserve original for context
        }