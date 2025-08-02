import re
import time
from typing import Dict, List, Optional, Tuple

def extract_playlist_id_from_url(playlist_url: str) -> Optional[str]:
    """Extract playlist ID from Spotify playlist URL"""
    if not playlist_url:
        return None
    
    # Handle different URL formats
    patterns = [
        r'spotify\.com/playlist/([a-zA-Z0-9]+)',
        r'playlist/([a-zA-Z0-9]+)',
        r'([a-zA-Z0-9]{22})'  # Spotify IDs are 22 characters
    ]
    
    for pattern in patterns:
        match = re.search(pattern, playlist_url)
        if match:
            return match.group(1)
    
    return None

def rank_recommendations_fast(recommendations: List[Dict], user_preferences: Dict = None) -> List[Dict]:
    """Fast ranking of recommendations based on user preferences"""
    if not recommendations:
        return []
    
    # Simple scoring based on popularity and user preferences
    for rec in recommendations:
        score = 0.0
        
        # Base score from popularity
        popularity = rec.get('popularity', 0.5)
        score += popularity * 0.4
        
        # Genre preference bonus
        if user_preferences and 'genres' in user_preferences:
            user_genres = [g.lower() for g in user_preferences['genres']]
            rec_genre = rec.get('primary_genre', '').lower()
            if rec_genre in user_genres:
                score += 0.3
        
        # Artist preference bonus
        if user_preferences and 'artists' in user_preferences:
            user_artists = [a.lower() for a in user_preferences['artists']]
            rec_artist = rec.get('name', '').lower()
            if rec_artist in user_artists:
                score += 0.3
        
        rec['ranking_score'] = score
    
    # Sort by ranking score
    return sorted(recommendations, key=lambda x: x.get('ranking_score', 0), reverse=True)

def apply_cultural_intelligence_fast(recommendations: List[Dict], user_country: str) -> List[Dict]:
    """Apply cultural intelligence to recommendations (fast version)"""
    if not recommendations or not user_country:
        return recommendations
    
    # Simple cultural adjustments based on country
    cultural_boost = {
        'IN': 0.2,  # India
        'PK': 0.2,  # Pakistan
        'BD': 0.2,  # Bangladesh
        'LK': 0.2,  # Sri Lanka
        'NP': 0.2,  # Nepal
        'KR': 0.15, # South Korea
        'JP': 0.15, # Japan
        'CN': 0.15, # China
        'MX': 0.1,  # Mexico
        'BR': 0.1,  # Brazil
    }
    
    boost = cultural_boost.get(user_country.upper(), 0.0)
    
    for rec in recommendations:
        current_score = rec.get('ranking_score', 0.0)
        rec['ranking_score'] = current_score + boost
    
    return recommendations

def get_fallback_recommendations(context_type: str) -> List[Dict]:
    """Get fallback recommendations when APIs fail"""
    fallback_data = {
        "party": [
            {"name": "The Weeknd", "popularity": 0.9, "primary_genre": "pop"},
            {"name": "Dua Lipa", "popularity": 0.8, "primary_genre": "pop"},
            {"name": "Bad Bunny", "popularity": 0.9, "primary_genre": "latin"},
            {"name": "Taylor Swift", "popularity": 0.9, "primary_genre": "pop"},
            {"name": "Drake", "popularity": 0.9, "primary_genre": "hip hop"}
        ],
        "study": [
            {"name": "Lofi Girl", "popularity": 0.7, "primary_genre": "ambient"},
            {"name": "Chillhop Music", "popularity": 0.6, "primary_genre": "jazz"},
            {"name": "Peaceful Piano", "popularity": 0.6, "primary_genre": "classical"},
            {"name": "Deep Focus", "popularity": 0.7, "primary_genre": "ambient"},
            {"name": "Nature Sounds", "popularity": 0.5, "primary_genre": "ambient"}
        ],
        "workout": [
            {"name": "The Weeknd", "popularity": 0.9, "primary_genre": "pop"},
            {"name": "Dua Lipa", "popularity": 0.8, "primary_genre": "pop"},
            {"name": "Post Malone", "popularity": 0.8, "primary_genre": "pop"},
            {"name": "Ariana Grande", "popularity": 0.9, "primary_genre": "pop"},
            {"name": "Drake", "popularity": 0.9, "primary_genre": "hip hop"}
        ],
        "relaxation": [
            {"name": "Lofi Girl", "popularity": 0.7, "primary_genre": "ambient"},
            {"name": "Chillhop Music", "popularity": 0.6, "primary_genre": "jazz"},
            {"name": "Peaceful Piano", "popularity": 0.6, "primary_genre": "classical"},
            {"name": "Nature Sounds", "popularity": 0.5, "primary_genre": "ambient"},
            {"name": "Ambient Music", "popularity": 0.6, "primary_genre": "ambient"}
        ],
        "romantic": [
            {"name": "Ed Sheeran", "popularity": 0.8, "primary_genre": "pop"},
            {"name": "Adele", "popularity": 0.9, "primary_genre": "pop"},
            {"name": "John Legend", "popularity": 0.7, "primary_genre": "r&b"},
            {"name": "Sam Smith", "popularity": 0.8, "primary_genre": "pop"},
            {"name": "Lewis Capaldi", "popularity": 0.7, "primary_genre": "pop"}
        ]
    }
    
    return fallback_data.get(context_type, fallback_data["party"])

def sort_by_relevance(entities: List[Dict], user_preferences: Dict = None) -> List[Dict]:
    """Sort entities by relevance to user preferences"""
    if not entities:
        return []
    
    # Simple relevance scoring
    for entity in entities:
        relevance_score = 0.0
        
        # Base score from popularity
        popularity = entity.get('popularity', 0.5)
        relevance_score += popularity * 0.3
        
        # Genre match bonus
        if user_preferences and 'genres' in user_preferences:
            user_genres = [g.lower() for g in user_preferences['genres']]
            entity_genre = entity.get('primary_genre', '').lower()
            if entity_genre in user_genres:
                relevance_score += 0.4
        
        # Artist match bonus
        if user_preferences and 'artists' in user_preferences:
            user_artists = [a.lower() for a in user_preferences['artists']]
            entity_artist = entity.get('name', '').lower()
            if entity_artist in user_artists:
                relevance_score += 0.3
        
        entity['relevance_score'] = relevance_score
    
    # Sort by relevance score
    return sorted(entities, key=lambda x: x.get('relevance_score', 0), reverse=True)

def get_context_keywords(context_type: str) -> List[str]:
    """Get keywords for context type"""
    context_keywords = {
        "workout": ["energetic", "motivational", "pump", "energy", "fast"],
        "study": ["focus", "concentration", "calm", "ambient", "instrumental"],
        "party": ["dance", "upbeat", "fun", "celebration", "vibe"],
        "relaxation": ["chill", "calm", "peaceful", "ambient", "soft"],
        "romantic": ["love", "romantic", "intimate", "passionate", "sweet"],
        "general": ["popular", "mainstream", "trending", "hit", "chart"]
    }
    
    return context_keywords.get(context_type, ["popular", "mainstream"])

def get_cultural_keywords(user_country: str, location: str = None) -> List[str]:
    """Get cultural keywords for location"""
    cultural_keywords = {
        "US": ["american", "pop", "hip hop", "country"],
        "UK": ["british", "pop", "rock", "indie"],
        "JP": ["japanese", "j-pop", "j-rock", "anime"],
        "KR": ["korean", "k-pop", "k-hip hop"],
        "IN": ["indian", "bollywood", "indian pop"],
        "BR": ["brazilian", "samba", "bossa nova"],
        "MX": ["mexican", "mexican pop", "ranchera"],
        "FR": ["french", "french pop", "chanson"],
        "DE": ["german", "german pop", "schlager"],
        "IT": ["italian", "italian pop", "opera"]
    }
    
    return cultural_keywords.get(user_country.upper(), ["international", "global"])

def validate_input_data(data: Dict) -> Tuple[bool, str]:
    """Validate input data for recommendations"""
    required_fields = ['user_context', 'user_country']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
        
        if not data[field] or not isinstance(data[field], str):
            return False, f"Invalid {field}: must be non-empty string"
    
    # Validate user_context length
    if len(data['user_context']) > 500:
        return False, "user_context too long (max 500 characters)"
    
    # Validate user_country format (should be 2-letter country code)
    if len(data['user_country']) != 2:
        return False, "user_country must be 2-letter country code"
    
    return True, "Valid"

def sanitize_string(input_string: str) -> str:
    """Sanitize string input"""
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = input_string.replace("'", "").replace('"', "").replace(";", "").replace("--", "")
    
    # Limit length
    return sanitized[:1000] 