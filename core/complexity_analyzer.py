"""
Complexity Analyzer - Dynamic complexity scoring for intelligent routing
Production-grade system that understands app complexity beyond simple keywords
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

class AppType(Enum):
    """Base app types with inherent complexity"""
    TIMER = "timer"
    COUNTER = "counter"
    CALCULATOR = "calculator"
    TODO = "todo"
    NOTES = "notes"
    WEATHER = "weather"
    CHAT = "chat"
    SOCIAL = "social"
    ECOMMERCE = "ecommerce"
    GAME = "game"
    PRODUCTIVITY = "productivity"
    UTILITY = "utility"
    CUSTOM = "custom"

@dataclass
class ComplexityScore:
    """Detailed complexity analysis result"""
    total: int  # 0-100 score
    base_score: int  # From app type
    feature_score: int  # From features
    technical_score: int  # From technical requirements
    ui_score: int  # From UI complexity
    
    # Detailed breakdowns
    detected_features: List[str] = field(default_factory=list)
    technical_requirements: List[str] = field(default_factory=list)
    ui_elements: List[str] = field(default_factory=list)
    external_dependencies: List[str] = field(default_factory=list)
    
    # Modifiers
    has_authentication: bool = False
    has_networking: bool = False
    has_persistence: bool = False
    has_real_time: bool = False
    has_animations: bool = False
    
    # Complexity category
    @property
    def category(self) -> str:
        if self.total < 30:
            return "simple"
        elif self.total < 60:
            return "medium"
        else:
            return "complex"
    
    @property
    def recommended_model(self) -> str:
        """Recommend best LLM based on complexity"""
        if self.total < 30:
            return "grok"  # Fast, simple
        elif self.total < 70:
            return "gpt4"  # Balanced
        else:
            return "claude"  # Complex architecture

class ComplexityAnalyzer:
    """Production-grade complexity analyzer with nuanced scoring"""
    
    def __init__(self):
        # Base complexity scores for app types
        self.base_scores = {
            AppType.TIMER: 10,
            AppType.COUNTER: 8,
            AppType.CALCULATOR: 15,
            AppType.TODO: 20,
            AppType.NOTES: 18,
            AppType.WEATHER: 25,
            AppType.CHAT: 35,
            AppType.SOCIAL: 40,
            AppType.ECOMMERCE: 45,
            AppType.GAME: 30,
            AppType.PRODUCTIVITY: 35,
            AppType.UTILITY: 20,
            AppType.CUSTOM: 25
        }
        
        # Feature complexity modifiers
        self.feature_modifiers = {
            # Authentication & User Management
            'authentication': 25,
            'login': 20,
            'user profile': 15,
            'registration': 15,
            'oauth': 30,
            'biometric': 20,
            
            # Data & Storage
            'database': 20,
            'core data': 25,
            'cloudkit': 30,
            'firebase': 25,
            'realm': 20,
            'cache': 10,
            'offline': 15,
            
            # Networking
            'api': 15,
            'rest api': 15,
            'graphql': 25,
            'websocket': 30,
            'real-time': 25,
            'sync': 20,
            'push notification': 25,
            
            # UI Complexity
            'animation': 15,
            'animations': 15,
            'beautiful animation': 20,
            'beautiful animations': 20,
            'custom animation': 25,
            'gesture': 15,
            'drag and drop': 20,
            'charts': 20,
            'graphs': 20,
            'map': 25,
            'camera': 20,
            'photo': 15,
            'video': 25,
            'ar': 35,
            
            # Advanced Features
            'machine learning': 35,
            'ai': 30,
            'speech': 25,
            'voice': 20,
            'payment': 30,
            'in-app purchase': 25,
            'subscription': 20,
            'sharing': 10,
            'export': 10,
            'import': 10,
            
            # Architecture
            'mvvm': 10,
            'coordinator': 15,
            'dependency injection': 20,
            'modular': 15,
            
            # Complexity Reducers (negative scores)
            'simple': -10,
            'basic': -8,
            'minimal': -8,
            'prototype': -5,
            'demo': -5,
            'example': -5
        }
        
        # UI element complexity
        self.ui_complexity = {
            'tab': 5,
            'navigation': 5,
            'modal': 5,
            'sheet': 5,
            'popover': 8,
            'sidebar': 10,
            'split view': 12,
            'collection': 10,
            'grid': 10,
            'carousel': 12,
            'timeline': 15,
            'calendar': 20,
            'picker': 5,
            'slider': 3,
            'toggle': 2,
            'form': 10,
            'search': 8,
            'filter': 10,
            'sort': 8
        }
    
    def analyze(self, description: str, app_name: str = "") -> ComplexityScore:
        """
        Analyze app complexity from description
        Returns detailed complexity score and breakdown
        """
        description_lower = description.lower()
        combined = f"{description} {app_name}".lower()
        
        # Detect app type
        app_type = self._detect_app_type(combined)
        base_score = self.base_scores.get(app_type, 25)
        
        # Analyze features
        feature_score, features = self._analyze_features(description_lower)
        
        # Analyze technical requirements
        tech_score, tech_reqs = self._analyze_technical(description_lower)
        
        # Analyze UI complexity
        ui_score, ui_elements = self._analyze_ui(description_lower)
        
        # Detect special requirements
        has_auth = self._has_authentication(description_lower)
        has_network = self._has_networking(description_lower)
        has_persist = self._has_persistence(description_lower)
        has_realtime = self._has_realtime(description_lower)
        has_anim = self._has_animations(description_lower)
        
        # Calculate total score (cap at 100)
        total = min(100, max(0, base_score + feature_score + tech_score + ui_score))
        
        # Apply complexity modifiers for specific combinations
        total = self._apply_combination_modifiers(
            total, features, tech_reqs, ui_elements
        )
        
        return ComplexityScore(
            total=max(0, total),  # Ensure non-negative
            base_score=base_score,
            feature_score=feature_score,
            technical_score=tech_score,
            ui_score=ui_score,
            detected_features=features,
            technical_requirements=tech_reqs,
            ui_elements=ui_elements,
            has_authentication=has_auth,
            has_networking=has_network,
            has_persistence=has_persist,
            has_real_time=has_realtime,
            has_animations=has_anim
        )
    
    def _detect_app_type(self, text: str) -> AppType:
        """Detect base app type from description"""
        type_patterns = {
            AppType.TIMER: r'\b(timer|countdown|stopwatch|alarm)\b',
            AppType.COUNTER: r'\b(counter|tally|count|increment|decrement)\b',
            AppType.CALCULATOR: r'\b(calculator|calculation|compute|math)\b',
            AppType.TODO: r'\b(todo|task|checklist|to-do)\b',
            AppType.NOTES: r'\b(notes?|memo|journal|diary)\b',
            AppType.WEATHER: r'\b(weather|climate|forecast|temperature)\b',
            AppType.CHAT: r'\b(chat|message|messaging|conversation)\b',
            AppType.SOCIAL: r'\b(social|feed|post|follow|like|share)\b',
            AppType.ECOMMERCE: r'\b(shop|store|product|cart|checkout|order)\b',
            AppType.GAME: r'\b(game|play|score|level|puzzle)\b',
            AppType.PRODUCTIVITY: r'\b(productivity|workflow|organize|manage)\b',
            AppType.UTILITY: r'\b(utility|tool|converter|scanner)\b'
        }
        
        for app_type, pattern in type_patterns.items():
            if re.search(pattern, text):
                return app_type
        
        return AppType.CUSTOM
    
    def _analyze_features(self, text: str) -> Tuple[int, List[str]]:
        """Analyze feature complexity"""
        score = 0
        detected = []
        
        for feature, modifier in self.feature_modifiers.items():
            # Use word boundaries for more accurate detection
            pattern = r'\b' + re.escape(feature) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                score += modifier
                if modifier > 0:  # Only track positive features
                    detected.append(feature)
        
        return score, detected
    
    def _analyze_technical(self, text: str) -> Tuple[int, List[str]]:
        """Analyze technical requirements"""
        tech_patterns = {
            'async/await': (10, r'\basync|await|concurrent\b'),
            'combine': (15, r'\bcombine|publisher|subscriber\b'),
            'swiftui': (5, r'\bswiftui\b'),
            'uikit': (10, r'\buikit\b'),
            'metal': (25, r'\bmetal|gpu\b'),
            'core motion': (20, r'\bmotion|accelerometer|gyroscope\b'),
            'healthkit': (25, r'\bhealthkit|health\sdata\b'),
            'homekit': (25, r'\bhomekit|smart\shome\b'),
            'sirikit': (20, r'\bsiri|voice\sassistant\b'),
            'widgets': (20, r'\bwidget|home\sscreen\b'),
            'watch app': (30, r'\bwatch\sapp|watchos\b'),
            'ipad': (15, r'\bipad|tablet\b'),
            'mac catalyst': (20, r'\bmac|catalyst|desktop\b')
        }
        
        score = 0
        detected = []
        
        for tech, (modifier, pattern) in tech_patterns.items():
            if re.search(pattern, text):
                score += modifier
                detected.append(tech)
        
        return score, detected
    
    def _analyze_ui(self, text: str) -> Tuple[int, List[str]]:
        """Analyze UI complexity"""
        score = 0
        detected = []
        
        for element, modifier in self.ui_complexity.items():
            # More precise matching with word boundaries where appropriate
            if element in ['search', 'filter', 'sort', 'form']:
                pattern = r'\b' + element + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    score += modifier
                    detected.append(element)
            elif element in text:
                score += modifier
                detected.append(element)
        
        # Check for multiple screens/views
        if re.search(r'\b(multiple|several|many)\s+(screens?|views?|pages?)\b', text):
            score += 15
            detected.append('multiple screens')
        
        return score, detected
    
    def _has_authentication(self, text: str) -> bool:
        """Check if app requires authentication"""
        auth_patterns = r'\b(auth|login|signin|signup|register|user\saccount|password|oauth|biometric)\b'
        return bool(re.search(auth_patterns, text))
    
    def _has_networking(self, text: str) -> bool:
        """Check if app requires networking"""
        network_patterns = r'\b(api|rest|graphql|websocket|http|network|online|cloud|sync|fetch|download|upload)\b'
        return bool(re.search(network_patterns, text))
    
    def _has_persistence(self, text: str) -> bool:
        """Check if app requires data persistence"""
        persist_patterns = r'\b(save|store|database|cache|persist|core\sdata|realm|sqlite|offline|local\sstorage)\b'
        return bool(re.search(persist_patterns, text))
    
    def _has_realtime(self, text: str) -> bool:
        """Check if app requires real-time features"""
        realtime_patterns = r'\b(real[\s-]?time|live|stream|websocket|push|instant|sync)\b'
        return bool(re.search(realtime_patterns, text))
    
    def _has_animations(self, text: str) -> bool:
        """Check if app requires animations"""
        animation_patterns = r'\b(animat|transition|gesture|drag|swipe|bounce|spring|fade|slide)\b'
        return bool(re.search(animation_patterns, text))
    
    def _apply_combination_modifiers(
        self, 
        score: int, 
        features: List[str], 
        tech: List[str], 
        ui: List[str]
    ) -> int:
        """Apply modifiers for specific feature combinations"""
        
        # Complex feature combinations
        if 'authentication' in features and 'api' in features:
            score += 10  # Auth + API = more complex
        
        if 'real-time' in features and 'database' in features:
            score += 15  # Real-time + DB = complex sync
        
        if len(ui) > 5:
            score += 10  # Many UI elements = complex navigation
        
        if len(features) > 8:
            score += 15  # Feature-rich app
        
        # Cap complexity for explicitly simple requests
        if 'simple' in features or 'basic' in features:
            score = min(score, 40)  # Cap at medium complexity
        
        return score
    
    def get_recommendation(self, score: ComplexityScore) -> Dict[str, any]:
        """Get recommendations based on complexity analysis"""
        return {
            'model': score.recommended_model,
            'max_tokens': 8192 if score.total > 60 else 4096,
            'temperature': 0.7 if score.total < 30 else 0.5,
            'retry_attempts': 5 if score.total > 70 else 3,
            'timeout': 60 if score.total > 60 else 30,
            'use_staged_generation': score.total > 50,
            'validation_level': 'comprehensive' if score.total > 60 else 'standard'
        }

