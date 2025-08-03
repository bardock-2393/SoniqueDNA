import time
import random
from typing import Dict, List, Optional
import os

class MusicAggregatorService:
    """Aggregates music from multiple providers for maximum variety and global discovery"""
    
    def __init__(self):
        # Initialize all music providers
        self.providers = {}
        self._initialize_providers()
        
        # Global music variety settings
        self.variety_settings = {
            "max_providers_per_request": 3,
            "min_artists_per_provider": 5,
            "max_total_artists": 50,
            "variety_boost_factor": 1.5,
            "cultural_diversity_weight": 0.3,
            "mood_diversity_weight": 0.2,
            "genre_diversity_weight": 0.5
        }
        
        # Global music categories for enhanced variety
        self.global_categories = {
            "korean": {
                "keywords": ["k-pop", "korean pop", "korean hip hop", "korean r&b", "korean indie"],
                "regions": ["KR", "Korea", "South Korea"],
                "languages": ["korean", "ko"],
                "weight": 0.9
            },
            "japanese": {
                "keywords": ["j-pop", "japanese pop", "japanese rock", "anime music", "japanese indie"],
                "regions": ["JP", "Japan"],
                "languages": ["japanese", "ja"],
                "weight": 0.9
            },
            "indian": {
                "keywords": ["bollywood", "indian pop", "punjabi", "tamil", "telugu", "bengali", "hindi"],
                "regions": ["IN", "India"],
                "languages": ["hindi", "punjabi", "tamil", "telugu", "bengali"],
                "weight": 0.8
            },
            "latin": {
                "keywords": ["reggaeton", "latin pop", "salsa", "bachata", "merengue", "spanish"],
                "regions": ["ES", "MX", "AR", "CO", "PE", "Latin America"],
                "languages": ["spanish", "es"],
                "weight": 0.8
            },
            "african": {
                "keywords": ["afrobeats", "amapiano", "african pop", "nigerian music", "ghanaian"],
                "regions": ["NG", "GH", "ZA", "KE", "Africa"],
                "languages": ["english", "yoruba", "igbo", "swahili"],
                "weight": 0.7
            },
            "arabic": {
                "keywords": ["arabic pop", "middle eastern", "turkish pop", "persian music", "egyptian"],
                "regions": ["EG", "TR", "SA", "AE", "Middle East"],
                "languages": ["arabic", "turkish", "persian"],
                "weight": 0.7
            },
            "chinese": {
                "keywords": ["mandopop", "chinese pop", "cantopop", "mandarin", "chinese rock"],
                "regions": ["CN", "TW", "HK", "China"],
                "languages": ["mandarin", "cantonese", "zh"],
                "weight": 0.8
            },
            "thai": {
                "keywords": ["thai pop", "luk thung", "thai rock", "thai indie"],
                "regions": ["TH", "Thailand"],
                "languages": ["thai"],
                "weight": 0.6
            },
            "vietnamese": {
                "keywords": ["vietnamese pop", "v-pop", "vietnamese rock"],
                "regions": ["VN", "Vietnam"],
                "languages": ["vietnamese", "vi"],
                "weight": 0.6
            },
            "filipino": {
                "keywords": ["opm", "filipino pop", "tagalog", "filipino rock"],
                "regions": ["PH", "Philippines"],
                "languages": ["tagalog", "filipino"],
                "weight": 0.6
            },
            "european": {
                "keywords": ["europop", "french pop", "german pop", "italian pop", "dutch pop"],
                "regions": ["FR", "DE", "IT", "NL", "Europe"],
                "languages": ["french", "german", "italian", "dutch"],
                "weight": 0.7
            },
            "caribbean": {
                "keywords": ["dancehall", "soca", "calypso", "reggae", "caribbean"],
                "regions": ["JM", "TT", "BB", "Caribbean"],
                "languages": ["english", "patois"],
                "weight": 0.6
            }
        }
        
        # Enhanced mood categories
        self.mood_categories = {
            "happy": {
                "keywords": ["happy", "upbeat", "feel good", "positive", "joyful"],
                "energy_level": "high",
                "valence": "positive",
                "weight": 0.8
            },
            "sad": {
                "keywords": ["sad", "melancholic", "emotional", "depressing", "blue"],
                "energy_level": "low",
                "valence": "negative",
                "weight": 0.7
            },
            "energetic": {
                "keywords": ["energetic", "high energy", "powerful", "intense", "dynamic"],
                "energy_level": "very_high",
                "valence": "positive",
                "weight": 0.9
            },
            "calm": {
                "keywords": ["calm", "relaxing", "peaceful", "ambient", "chill"],
                "energy_level": "very_low",
                "valence": "neutral",
                "weight": 0.6
            },
            "romantic": {
                "keywords": ["romantic", "love", "romance", "passionate", "intimate"],
                "energy_level": "medium",
                "valence": "positive",
                "weight": 0.8
            },
            "party": {
                "keywords": ["party", "dance", "club", "festival", "celebration"],
                "energy_level": "very_high",
                "valence": "positive",
                "weight": 0.9
            },
            "motivational": {
                "keywords": ["motivational", "inspirational", "uplifting", "empowering"],
                "energy_level": "high",
                "valence": "positive",
                "weight": 0.8
            },
            "nostalgic": {
                "keywords": ["nostalgic", "retro", "throwback", "vintage", "classic"],
                "energy_level": "medium",
                "valence": "neutral",
                "weight": 0.7
            }
        }
    
    def _initialize_providers(self):
        """Initialize all available music providers"""
        try:
            # Import providers dynamically to handle missing APIs gracefully
            from services.youtube import YouTubeMusicService
            self.providers["youtube"] = YouTubeMusicService()
            print("✓ YouTube Music provider initialized")
        except Exception as e:
            print(f"✗ YouTube Music provider failed: {e}")
        
        try:
            from services.lastfm import LastFMService
            self.providers["lastfm"] = LastFMService()
            print("✓ Last.fm provider initialized")
        except Exception as e:
            print(f"✗ Last.fm provider failed: {e}")
        
        try:
            from services.deezer import DeezerService
            self.providers["deezer"] = DeezerService()
            print("✓ Deezer provider initialized")
        except Exception as e:
            print(f"✗ Deezer provider failed: {e}")
        
        print(f"Total providers available: {len(self.providers)}")
    
    def get_global_music_variety(self, 
                                category: str = None, 
                                mood: str = None, 
                                region: str = None, 
                                limit: int = 30,
                                variety_boost: bool = True) -> Dict:
        """Get diverse global music from multiple providers with enhanced variety"""
        
        start_time = time.time()
        all_artists = []
        provider_results = {}
        
        print(f"[AGGREGATOR] Starting global music variety search")
        print(f"[AGGREGATOR] Category: {category}, Mood: {mood}, Region: {region}, Limit: {limit}")
        
        # Select providers for this request
        available_providers = list(self.providers.keys())
        selected_providers = self._select_providers(available_providers, category, mood)
        
        print(f"[AGGREGATOR] Selected providers: {selected_providers}")
        
        # Get music from each provider
        for provider_name in selected_providers:
            try:
                provider = self.providers[provider_name]
                provider_limit = max(self.variety_settings["min_artists_per_provider"], 
                                   limit // len(selected_providers))
                
                print(f"[AGGREGATOR] Querying {provider_name} for {provider_limit} artists...")
                
                if category and mood:
                    # Try category-specific search first
                    artists = provider.get_global_music_variety(category, provider_limit)
                    if len(artists) < provider_limit // 2:
                        # Fallback to mood-based search
                        mood_artists = provider.get_music_by_mood(mood, provider_limit)
                        artists.extend(mood_artists)
                elif category:
                    artists = provider.get_global_music_variety(category, provider_limit)
                elif mood:
                    artists = provider.get_music_by_mood(mood, provider_limit)
                else:
                    # Get general variety
                    artists = provider.get_global_music_variety(None, provider_limit)
                
                # Add provider metadata
                for artist in artists:
                    artist["provider"] = provider_name
                    artist["variety_score"] = self._calculate_variety_score(artist, category, mood, region)
                
                provider_results[provider_name] = artists
                all_artists.extend(artists)
                
                print(f"[AGGREGATOR] {provider_name} returned {len(artists)} artists")
                
            except Exception as e:
                print(f"[AGGREGATOR] Error with {provider_name}: {e}")
                continue
        
        # Apply variety enhancement
        if variety_boost and len(all_artists) > 0:
            all_artists = self._apply_variety_enhancement(all_artists, category, mood, region)
        
        # Remove duplicates and sort by variety score
        unique_artists = self._remove_duplicates_and_sort(all_artists)
        
        # Limit results
        final_artists = unique_artists[:limit]
        
        # Calculate variety statistics
        variety_stats = self._calculate_variety_statistics(final_artists, provider_results)
        
        response_time = time.time() - start_time
        
        return {
            "artists": final_artists,
            "providers_used": selected_providers,
            "total_artists_found": len(all_artists),
            "unique_artists_returned": len(final_artists),
            "variety_stats": variety_stats,
            "provider_results": provider_results,
            "response_time": round(response_time, 2),
            "category": category,
            "mood": mood,
            "region": region,
            "variety_boost_applied": variety_boost
        }
    
    def get_cultural_music_variety(self, culture: str, limit: int = 25) -> Dict:
        """Get music from specific cultural background with variety"""
        
        start_time = time.time()
        all_artists = []
        provider_results = {}
        
        print(f"[AGGREGATOR] Getting cultural music variety for: {culture}")
        
        # Get cultural keywords
        cultural_info = self.global_categories.get(culture.lower(), {})
        keywords = cultural_info.get("keywords", [culture])
        
        # Select providers
        available_providers = list(self.providers.keys())
        selected_providers = self._select_providers(available_providers, culture, None)
        
        for provider_name in selected_providers:
            try:
                provider = self.providers[provider_name]
                provider_limit = max(self.variety_settings["min_artists_per_provider"], 
                                   limit // len(selected_providers))
                
                # Try different approaches for cultural music
                artists = []
                
                if hasattr(provider, 'get_cultural_music'):
                    artists = provider.get_cultural_music(culture, provider_limit)
                elif hasattr(provider, 'get_global_music_variety'):
                    artists = provider.get_global_music_variety(culture, provider_limit)
                else:
                    # Fallback to search
                    for keyword in keywords[:3]:
                        if hasattr(provider, 'search_artists'):
                            keyword_artists = provider.search_artists(keyword, provider_limit // 3)
                            artists.extend(keyword_artists)
                
                # Add metadata
                for artist in artists:
                    artist["provider"] = provider_name
                    artist["culture"] = culture
                    artist["variety_score"] = self._calculate_cultural_variety_score(artist, culture)
                
                provider_results[provider_name] = artists
                all_artists.extend(artists)
                
            except Exception as e:
                print(f"[AGGREGATOR] Error with {provider_name} for culture {culture}: {e}")
                continue
        
        # Apply cultural variety enhancement
        unique_artists = self._remove_duplicates_and_sort(all_artists)
        final_artists = unique_artists[:limit]
        
        variety_stats = self._calculate_cultural_variety_statistics(final_artists, culture)
        
        response_time = time.time() - start_time
        
        return {
            "artists": final_artists,
            "culture": culture,
            "cultural_keywords": keywords,
            "providers_used": selected_providers,
            "total_artists_found": len(all_artists),
            "unique_artists_returned": len(final_artists),
            "variety_stats": variety_stats,
            "response_time": round(response_time, 2)
        }
    
    def get_mood_based_variety(self, mood: str, limit: int = 25) -> Dict:
        """Get music based on mood with enhanced variety"""
        
        start_time = time.time()
        all_artists = []
        provider_results = {}
        
        print(f"[AGGREGATOR] Getting mood-based variety for: {mood}")
        
        # Get mood information
        mood_info = self.mood_categories.get(mood.lower(), {})
        keywords = mood_info.get("keywords", [mood])
        
        # Select providers
        available_providers = list(self.providers.keys())
        selected_providers = self._select_providers(available_providers, None, mood)
        
        for provider_name in selected_providers:
            try:
                provider = self.providers[provider_name]
                provider_limit = max(self.variety_settings["min_artists_per_provider"], 
                                   limit // len(selected_providers))
                
                # Try mood-specific method first
                artists = []
                if hasattr(provider, 'get_music_by_mood'):
                    artists = provider.get_music_by_mood(mood, provider_limit)
                else:
                    # Fallback to search
                    for keyword in keywords[:3]:
                        if hasattr(provider, 'search_artists'):
                            keyword_artists = provider.search_artists(keyword, provider_limit // 3)
                            artists.extend(keyword_artists)
                
                # Add metadata
                for artist in artists:
                    artist["provider"] = provider_name
                    artist["mood"] = mood
                    artist["variety_score"] = self._calculate_mood_variety_score(artist, mood)
                
                provider_results[provider_name] = artists
                all_artists.extend(artists)
                
            except Exception as e:
                print(f"[AGGREGATOR] Error with {provider_name} for mood {mood}: {e}")
                continue
        
        # Apply mood variety enhancement
        unique_artists = self._remove_duplicates_and_sort(all_artists)
        final_artists = unique_artists[:limit]
        
        variety_stats = self._calculate_mood_variety_statistics(final_artists, mood)
        
        response_time = time.time() - start_time
        
        return {
            "artists": final_artists,
            "mood": mood,
            "mood_keywords": keywords,
            "providers_used": selected_providers,
            "total_artists_found": len(all_artists),
            "unique_artists_returned": len(final_artists),
            "variety_stats": variety_stats,
            "response_time": round(response_time, 2)
        }
    
    def _select_providers(self, available_providers: List[str], category: str = None, mood: str = None) -> List[str]:
        """Select the best providers for the given request"""
        
        # Priority order based on request type
        if category and category in self.global_categories:
            # Cultural music - prioritize providers with cultural support
            provider_priority = ["youtube", "lastfm", "deezer"]
        elif mood and mood in self.mood_categories:
            # Mood-based music - prioritize providers with mood support
            provider_priority = ["lastfm", "deezer", "youtube"]
        else:
            # General variety - use all providers
            provider_priority = ["youtube", "lastfm", "deezer"]
        
        # Filter to available providers and limit count
        selected = []
        for provider in provider_priority:
            if provider in available_providers and len(selected) < self.variety_settings["max_providers_per_request"]:
                selected.append(provider)
        
        # If we don't have enough, add any remaining providers
        for provider in available_providers:
            if provider not in selected and len(selected) < self.variety_settings["max_providers_per_request"]:
                selected.append(provider)
        
        return selected
    
    def _calculate_variety_score(self, artist: Dict, category: str = None, mood: str = None, region: str = None) -> float:
        """Calculate variety score for an artist"""
        score = 1.0
        
        # Base score from provider
        if artist.get("source") == "youtube":
            score += 0.2
        elif artist.get("source") == "lastfm":
            score += 0.3
        elif artist.get("source") == "deezer":
            score += 0.2
        
        # Cultural relevance
        if category and category in self.global_categories:
            cultural_weight = self.global_categories[category].get("weight", 0.5)
            score += cultural_weight
        
        # Mood relevance
        if mood and mood in self.mood_categories:
            mood_weight = self.mood_categories[mood].get("weight", 0.5)
            score += mood_weight
        
        # Random factor for variety
        score += random.uniform(0, 0.3)
        
        return round(score, 3)
    
    def _calculate_cultural_variety_score(self, artist: Dict, culture: str) -> float:
        """Calculate cultural variety score"""
        score = 1.0
        
        cultural_info = self.global_categories.get(culture.lower(), {})
        cultural_weight = cultural_info.get("weight", 0.5)
        
        # Check if artist name contains cultural keywords
        artist_name = artist.get("name", "").lower()
        keywords = cultural_info.get("keywords", [])
        
        for keyword in keywords:
            if keyword.lower() in artist_name:
                score += cultural_weight
                break
        
        # Provider bonus
        if artist.get("source") == "youtube":
            score += 0.2
        elif artist.get("source") == "lastfm":
            score += 0.3
        
        score += random.uniform(0, 0.2)
        return round(score, 3)
    
    def _calculate_mood_variety_score(self, artist: Dict, mood: str) -> float:
        """Calculate mood variety score"""
        score = 1.0
        
        mood_info = self.mood_categories.get(mood.lower(), {})
        mood_weight = mood_info.get("weight", 0.5)
        
        # Check if artist name contains mood keywords
        artist_name = artist.get("name", "").lower()
        keywords = mood_info.get("keywords", [])
        
        for keyword in keywords:
            if keyword.lower() in artist_name:
                score += mood_weight
                break
        
        # Provider bonus
        if artist.get("source") == "lastfm":
            score += 0.3
        elif artist.get("source") == "deezer":
            score += 0.2
        
        score += random.uniform(0, 0.2)
        return round(score, 3)
    
    def _apply_variety_enhancement(self, artists: List[Dict], category: str = None, mood: str = None, region: str = None) -> List[Dict]:
        """Apply variety enhancement to artist list"""
        
        # Sort by variety score
        artists.sort(key=lambda x: x.get("variety_score", 0), reverse=True)
        
        # Ensure diversity across providers
        provider_counts = {}
        enhanced_artists = []
        
        for artist in artists:
            provider = artist.get("provider", "unknown")
            current_count = provider_counts.get(provider, 0)
            
            # Limit artists per provider for variety
            max_per_provider = len(artists) // len(set(a.get("provider") for a in artists)) + 2
            
            if current_count < max_per_provider:
                enhanced_artists.append(artist)
                provider_counts[provider] = current_count + 1
        
        # Shuffle for additional variety
        random.shuffle(enhanced_artists)
        
        return enhanced_artists
    
    def _remove_duplicates_and_sort(self, artists: List[Dict]) -> List[Dict]:
        """Remove duplicates and sort by variety score"""
        
        # Remove duplicates based on name
        seen_names = set()
        unique_artists = []
        
        for artist in artists:
            name = artist.get("name", "").lower().strip()
            if name and name not in seen_names:
                unique_artists.append(artist)
                seen_names.add(name)
        
        # Sort by variety score
        unique_artists.sort(key=lambda x: x.get("variety_score", 0), reverse=True)
        
        return unique_artists
    
    def _calculate_variety_statistics(self, artists: List[Dict], provider_results: Dict) -> Dict:
        """Calculate variety statistics"""
        
        providers_used = list(provider_results.keys())
        total_providers = len(providers_used)
        
        # Count artists by provider
        provider_counts = {}
        for artist in artists:
            provider = artist.get("provider", "unknown")
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        # Calculate average variety score
        variety_scores = [artist.get("variety_score", 0) for artist in artists]
        avg_variety_score = sum(variety_scores) / len(variety_scores) if variety_scores else 0
        
        return {
            "total_providers": total_providers,
            "providers_used": providers_used,
            "provider_distribution": provider_counts,
            "average_variety_score": round(avg_variety_score, 3),
            "max_variety_score": max(variety_scores) if variety_scores else 0,
            "min_variety_score": min(variety_scores) if variety_scores else 0,
            "total_categories_available": len(self.global_categories),
            "total_moods_available": len(self.mood_categories)
        }
    
    def _calculate_cultural_variety_statistics(self, artists: List[Dict], culture: str) -> Dict:
        """Calculate cultural variety statistics"""
        
        cultural_info = self.global_categories.get(culture.lower(), {})
        
        variety_scores = [artist.get("variety_score", 0) for artist in artists]
        avg_variety_score = sum(variety_scores) / len(variety_scores) if variety_scores else 0
        
        return {
            "culture": culture,
            "cultural_weight": cultural_info.get("weight", 0.5),
            "cultural_keywords": cultural_info.get("keywords", []),
            "average_variety_score": round(avg_variety_score, 3),
            "max_variety_score": max(variety_scores) if variety_scores else 0,
            "min_variety_score": min(variety_scores) if variety_scores else 0
        }
    
    def _calculate_mood_variety_statistics(self, artists: List[Dict], mood: str) -> Dict:
        """Calculate mood variety statistics"""
        
        mood_info = self.mood_categories.get(mood.lower(), {})
        
        variety_scores = [artist.get("variety_score", 0) for artist in artists]
        avg_variety_score = sum(variety_scores) / len(variety_scores) if variety_scores else 0
        
        return {
            "mood": mood,
            "mood_weight": mood_info.get("weight", 0.5),
            "energy_level": mood_info.get("energy_level", "medium"),
            "valence": mood_info.get("valence", "neutral"),
            "average_variety_score": round(avg_variety_score, 3),
            "max_variety_score": max(variety_scores) if variety_scores else 0,
            "min_variety_score": min(variety_scores) if variety_scores else 0
        }
    
    def get_variety_stats(self) -> Dict:
        """Get comprehensive variety statistics"""
        return {
            "total_providers": len(self.providers),
            "available_providers": list(self.providers.keys()),
            "total_categories": len(self.global_categories),
            "total_moods": len(self.mood_categories),
            "variety_settings": self.variety_settings,
            "source": "music_aggregator"
        } 