import requests
import time
import random
from typing import Dict, List, Optional
import os

class LastFMService:
    """Last.fm API service for global music discovery and variety"""
    
    def __init__(self):
        self.api_key = os.getenv('LASTFM_API_KEY')
        self.base_url = "https://ws.audioscrobbler.com/2.0/"
        
        # Global music tags for variety
        self.global_tags = {
            "korean": ["k-pop", "korean", "korean pop", "korean hip hop"],
            "japanese": ["j-pop", "japanese", "japanese pop", "anime"],
            "indian": ["bollywood", "indian", "punjabi", "tamil", "telugu"],
            "latin": ["reggaeton", "latin", "spanish", "salsa", "bachata"],
            "african": ["afrobeats", "african", "nigerian", "amapiano"],
            "arabic": ["arabic", "middle eastern", "turkish", "persian"],
            "chinese": ["mandopop", "chinese", "cantopop", "mandarin"],
            "thai": ["thai", "thai pop", "luk thung"],
            "vietnamese": ["vietnamese", "v-pop"],
            "filipino": ["opm", "filipino", "tagalog"]
        }
        
        # Mood-based tags
        self.mood_tags = {
            "happy": ["happy", "upbeat", "feel good", "positive"],
            "sad": ["sad", "melancholic", "emotional", "depressing"],
            "energetic": ["energetic", "high energy", "powerful", "intense"],
            "calm": ["calm", "relaxing", "peaceful", "ambient"],
            "romantic": ["romantic", "love", "romance", "passionate"],
            "party": ["party", "dance", "club", "festival"],
            "motivational": ["motivational", "inspirational", "uplifting"],
            "nostalgic": ["nostalgic", "retro", "throwback", "vintage"]
        }
    
    def search_artists(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for artists on Last.fm"""
        try:
            params = {
                "method": "artist.search",
                "artist": query,
                "api_key": self.api_key,
                "format": "json",
                "limit": limit
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                artists = []
                
                for artist in data.get("results", {}).get("artistmatches", {}).get("artist", []):
                    artist_info = {
                        "name": artist.get("name", ""),
                        "mbid": artist.get("mbid", ""),
                        "url": artist.get("url", ""),
                        "image": self._get_largest_image(artist.get("image", [])),
                        "listeners": artist.get("listeners", "0"),
                        "source": "lastfm"
                    }
                    artists.append(artist_info)
                
                return artists
            else:
                print(f"Last.fm API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Last.fm search error: {e}")
            return []
    
    def get_top_artists_by_tag(self, tag: str, limit: int = 15) -> List[Dict]:
        """Get top artists by tag"""
        try:
            params = {
                "method": "tag.gettopartists",
                "tag": tag,
                "api_key": self.api_key,
                "format": "json",
                "limit": limit
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                artists = []
                
                for artist in data.get("topartists", {}).get("artist", []):
                    artist_info = {
                        "name": artist.get("name", ""),
                        "mbid": artist.get("mbid", ""),
                        "url": artist.get("url", ""),
                        "image": self._get_largest_image(artist.get("image", [])),
                        "listeners": artist.get("listeners", "0"),
                        "tag": tag,
                        "source": "lastfm"
                    }
                    artists.append(artist_info)
                
                return artists
            else:
                print(f"Last.fm tag error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Last.fm tag error: {e}")
            return []
    
    def get_global_music_variety(self, category: str = None, limit: int = 20) -> List[Dict]:
        """Get diverse global music from different regions and categories"""
        try:
            all_artists = []
            
            if category and category in self.global_tags:
                # Get artists from specific category
                tags = self.global_tags[category]
                for tag in tags[:5]:
                    artists = self.get_top_artists_by_tag(tag, limit // 5)
                    all_artists.extend(artists)
                    time.sleep(0.5)  # Rate limiting
            else:
                # Get diverse artists from multiple categories
                categories = list(self.global_tags.keys())
                random.shuffle(categories)
                
                for cat in categories[:6]:  # Use 6 random categories
                    tags = self.global_tags[cat]
                    tag = random.choice(tags)
                    artists = self.get_top_artists_by_tag(tag, limit // 6)
                    all_artists.extend(artists)
                    time.sleep(0.5)
            
            # Remove duplicates and add variety
            unique_artists = self._remove_duplicates(all_artists)
            random.shuffle(unique_artists)
            
            return unique_artists[:limit]
            
        except Exception as e:
            print(f"Global music variety error: {e}")
            return []
    
    def get_music_by_mood(self, mood: str, limit: int = 15) -> List[Dict]:
        """Get music based on mood/emotion"""
        try:
            tags = self.mood_tags.get(mood.lower(), [mood])
            all_artists = []
            
            for tag in tags:
                artists = self.get_top_artists_by_tag(tag, limit // len(tags))
                all_artists.extend(artists)
                time.sleep(0.5)
            
            unique_artists = self._remove_duplicates(all_artists)
            random.shuffle(unique_artists)
            
            return unique_artists[:limit]
            
        except Exception as e:
            print(f"Mood music error: {e}")
            return []
    
    def get_similar_artists(self, artist_name: str, limit: int = 10) -> List[Dict]:
        """Get similar artists to a given artist"""
        try:
            params = {
                "method": "artist.getsimilar",
                "artist": artist_name,
                "api_key": self.api_key,
                "format": "json",
                "limit": limit
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                artists = []
                
                for artist in data.get("similarartists", {}).get("artist", []):
                    artist_info = {
                        "name": artist.get("name", ""),
                        "mbid": artist.get("mbid", ""),
                        "url": artist.get("url", ""),
                        "image": self._get_largest_image(artist.get("image", [])),
                        "match": artist.get("match", "0"),
                        "source": "lastfm",
                        "similar_to": artist_name
                    }
                    artists.append(artist_info)
                
                return artists
            else:
                print(f"Last.fm similar artists error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Similar artists error: {e}")
            return []
    
    def get_top_tracks_by_artist(self, artist_name: str, limit: int = 10) -> List[Dict]:
        """Get top tracks by artist"""
        try:
            params = {
                "method": "artist.gettoptracks",
                "artist": artist_name,
                "api_key": self.api_key,
                "format": "json",
                "limit": limit
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tracks = []
                
                for track in data.get("toptracks", {}).get("track", []):
                    track_info = {
                        "name": track.get("name", ""),
                        "artist": artist_name,
                        "playcount": track.get("playcount", "0"),
                        "url": track.get("url", ""),
                        "image": self._get_largest_image(track.get("image", [])),
                        "source": "lastfm"
                    }
                    tracks.append(track_info)
                
                return tracks
            else:
                print(f"Last.fm top tracks error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Top tracks error: {e}")
            return []
    
    def get_chart_top_artists(self, limit: int = 20) -> List[Dict]:
        """Get chart top artists globally"""
        try:
            params = {
                "method": "chart.gettopartists",
                "api_key": self.api_key,
                "format": "json",
                "limit": limit
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                artists = []
                
                for artist in data.get("artists", {}).get("artist", []):
                    artist_info = {
                        "name": artist.get("name", ""),
                        "mbid": artist.get("mbid", ""),
                        "url": artist.get("url", ""),
                        "image": self._get_largest_image(artist.get("image", [])),
                        "listeners": artist.get("listeners", "0"),
                        "playcount": artist.get("playcount", "0"),
                        "source": "lastfm",
                        "chart_position": len(artists) + 1
                    }
                    artists.append(artist_info)
                
                return artists
            else:
                print(f"Last.fm chart error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Chart error: {e}")
            return []
    
    def get_geo_top_artists(self, country: str, limit: int = 15) -> List[Dict]:
        """Get top artists by country"""
        try:
            params = {
                "method": "geo.gettopartists",
                "country": country,
                "api_key": self.api_key,
                "format": "json",
                "limit": limit
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                artists = []
                
                for artist in data.get("topartists", {}).get("artist", []):
                    artist_info = {
                        "name": artist.get("name", ""),
                        "mbid": artist.get("mbid", ""),
                        "url": artist.get("url", ""),
                        "image": self._get_largest_image(artist.get("image", [])),
                        "listeners": artist.get("listeners", "0"),
                        "country": country,
                        "source": "lastfm"
                    }
                    artists.append(artist_info)
                
                return artists
            else:
                print(f"Last.fm geo error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Geo top artists error: {e}")
            return []
    
    def _get_largest_image(self, images: List[Dict]) -> str:
        """Get the largest image URL from image array"""
        if not images:
            return ""
        
        # Sort by size (extralarge > large > medium > small)
        size_order = ["extralarge", "large", "medium", "small"]
        
        for size in size_order:
            for image in images:
                if image.get("size") == size:
                    return image.get("#text", "")
        
        # Fallback to first image
        return images[0].get("#text", "") if images else ""
    
    def _remove_duplicates(self, artists: List[Dict]) -> List[Dict]:
        """Remove duplicate artists based on name"""
        seen_names = set()
        unique_artists = []
        
        for artist in artists:
            name = artist.get("name", "").lower()
            if name and name not in seen_names:
                unique_artists.append(artist)
                seen_names.add(name)
        
        return unique_artists
    
    def get_variety_stats(self) -> Dict:
        """Get statistics about the variety of music sources"""
        return {
            "total_categories": len(self.global_tags),
            "total_moods": len(self.mood_tags),
            "cultural_variety": len(self.global_tags),
            "mood_variety": len(self.mood_tags),
            "source": "lastfm"
        } 