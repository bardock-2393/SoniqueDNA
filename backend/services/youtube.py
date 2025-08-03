import requests
import time
import random
from typing import Dict, List, Optional
import os
import re

class YouTubeMusicService:
    """YouTube Music API service for global music discovery and variety"""
    
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.headers = {"Accept": "application/json"}
        
        # Global music categories for variety
        self.global_music_categories = {
            "korean": ["k-pop", "korean pop", "korean hip hop", "korean r&b"],
            "japanese": ["j-pop", "japanese pop", "japanese rock", "anime music"],
            "indian": ["bollywood", "indian pop", "punjabi", "tamil", "telugu", "bengali"],
            "latin": ["reggaeton", "latin pop", "salsa", "bachata", "merengue"],
            "african": ["afrobeats", "amapiano", "african pop", "nigerian music"],
            "middle_eastern": ["arabic pop", "turkish pop", "persian music"],
            "european": ["europop", "french pop", "german pop", "italian pop"],
            "caribbean": ["dancehall", "soca", "calypso", "reggae"],
            "asian": ["mandopop", "cantopop", "thai pop", "vietnamese pop"]
        }
        
        # Trending music keywords by region
        self.trending_keywords = {
            "global": ["trending music", "viral songs", "popular music", "chart hits"],
            "korea": ["k-pop trending", "korean viral", "k-pop chart"],
            "japan": ["j-pop trending", "japanese viral", "anime music"],
            "india": ["bollywood trending", "indian viral", "punjabi trending"],
            "latin_america": ["reggaeton trending", "latin viral", "spanish music"],
            "africa": ["afrobeats trending", "african viral", "nigerian music"],
            "middle_east": ["arabic trending", "turkish viral", "persian music"]
        }
    
    def search_music_videos(self, query: str, max_results: int = 10, region_code: str = None) -> List[Dict]:
        """Search for music videos on YouTube"""
        try:
            params = {
                "part": "snippet",
                "q": f"{query} music",
                "type": "video",
                "videoCategoryId": "10",  # Music category
                "maxResults": max_results,
                "key": self.api_key
            }
            
            if region_code:
                params["regionCode"] = region_code
            
            response = requests.get(f"{self.base_url}/search", params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                videos = []
                
                for item in data.get("items", []):
                    video = {
                        "id": item["id"]["videoId"],
                        "title": item["snippet"]["title"],
                        "artist": self._extract_artist_from_title(item["snippet"]["title"]),
                        "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                        "published_at": item["snippet"]["publishedAt"],
                        "description": item["snippet"]["description"],
                        "channel_title": item["snippet"]["channelTitle"],
                        "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                        "source": "youtube",
                        "region": region_code or "global"
                    }
                    videos.append(video)
                
                return videos
            else:
                print(f"YouTube API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"YouTube search error: {e}")
            return []
    
    def get_trending_music_by_region(self, region: str = "global", max_results: int = 15) -> List[Dict]:
        """Get trending music videos by region"""
        try:
            keywords = self.trending_keywords.get(region, self.trending_keywords["global"])
            all_videos = []
            
            for keyword in keywords[:3]:  # Use top 3 keywords
                videos = self.search_music_videos(keyword, max_results // 3, region)
                all_videos.extend(videos)
                time.sleep(0.5)  # Rate limiting
            
            # Remove duplicates and shuffle for variety
            unique_videos = self._remove_duplicates(all_videos)
            random.shuffle(unique_videos)
            
            return unique_videos[:max_results]
            
        except Exception as e:
            print(f"Trending music error: {e}")
            return []
    
    def get_global_music_variety(self, category: str = None, max_results: int = 20) -> List[Dict]:
        """Get diverse global music from different regions and categories"""
        try:
            all_videos = []
            
            if category and category in self.global_music_categories:
                # Get music from specific category
                keywords = self.global_music_categories[category]
                for keyword in keywords[:5]:
                    videos = self.search_music_videos(keyword, max_results // 5)
                    all_videos.extend(videos)
                    time.sleep(0.5)
            else:
                # Get diverse music from multiple categories
                categories = list(self.global_music_categories.keys())
                random.shuffle(categories)
                
                for cat in categories[:6]:  # Use 6 random categories
                    keywords = self.global_music_categories[cat]
                    keyword = random.choice(keywords)
                    videos = self.search_music_videos(keyword, max_results // 6)
                    all_videos.extend(videos)
                    time.sleep(0.5)
            
            # Remove duplicates and add variety
            unique_videos = self._remove_duplicates(all_videos)
            random.shuffle(unique_videos)
            
            return unique_videos[:max_results]
            
        except Exception as e:
            print(f"Global music variety error: {e}")
            return []
    
    def search_by_artist(self, artist_name: str, max_results: int = 10) -> List[Dict]:
        """Search for music by specific artist"""
        try:
            # Try different search patterns for better results
            search_patterns = [
                f"{artist_name} official music video",
                f"{artist_name} live performance",
                f"{artist_name} latest song",
                f"{artist_name} popular songs"
            ]
            
            all_videos = []
            for pattern in search_patterns:
                videos = self.search_music_videos(pattern, max_results // 4)
                all_videos.extend(videos)
                time.sleep(0.5)
            
            # Remove duplicates
            unique_videos = self._remove_duplicates(all_videos)
            return unique_videos[:max_results]
            
        except Exception as e:
            print(f"Artist search error: {e}")
            return []
    
    def get_cultural_music(self, culture: str, max_results: int = 15) -> List[Dict]:
        """Get music from specific cultural background"""
        try:
            cultural_keywords = {
                "korean": ["k-pop", "korean traditional", "korean indie"],
                "japanese": ["j-pop", "japanese traditional", "anime music"],
                "indian": ["bollywood", "indian classical", "punjabi music"],
                "latin": ["reggaeton", "latin traditional", "spanish music"],
                "african": ["afrobeats", "african traditional", "nigerian music"],
                "arabic": ["arabic pop", "middle eastern", "turkish music"],
                "chinese": ["mandopop", "chinese traditional", "cantopop"],
                "thai": ["thai pop", "thai traditional", "luk thung"],
                "vietnamese": ["vietnamese pop", "vietnamese traditional"],
                "filipino": ["opm", "filipino pop", "tagalog music"]
            }
            
            keywords = cultural_keywords.get(culture.lower(), [culture])
            all_videos = []
            
            for keyword in keywords:
                videos = self.search_music_videos(keyword, max_results // len(keywords))
                all_videos.extend(videos)
                time.sleep(0.5)
            
            unique_videos = self._remove_duplicates(all_videos)
            random.shuffle(unique_videos)
            
            return unique_videos[:max_results]
            
        except Exception as e:
            print(f"Cultural music error: {e}")
            return []
    
    def get_music_by_mood(self, mood: str, max_results: int = 15) -> List[Dict]:
        """Get music based on mood/emotion"""
        try:
            mood_keywords = {
                "happy": ["happy music", "upbeat songs", "feel good music"],
                "sad": ["sad music", "melancholic songs", "emotional music"],
                "energetic": ["energetic music", "workout songs", "high energy"],
                "calm": ["calm music", "relaxing songs", "peaceful music"],
                "romantic": ["romantic music", "love songs", "romantic ballads"],
                "party": ["party music", "dance songs", "club music"],
                "motivational": ["motivational music", "inspirational songs"],
                "nostalgic": ["nostalgic music", "throwback songs", "retro music"]
            }
            
            keywords = mood_keywords.get(mood.lower(), [mood])
            all_videos = []
            
            for keyword in keywords:
                videos = self.search_music_videos(keyword, max_results // len(keywords))
                all_videos.extend(videos)
                time.sleep(0.5)
            
            unique_videos = self._remove_duplicates(all_videos)
            random.shuffle(unique_videos)
            
            return unique_videos[:max_results]
            
        except Exception as e:
            print(f"Mood music error: {e}")
            return []
    
    def _extract_artist_from_title(self, title: str) -> str:
        """Extract artist name from video title"""
        # Common patterns in music video titles
        patterns = [
            r'^([^-–—]+?)\s*[-–—]\s*',  # Artist - Song
            r'^([^-–—]+?)\s*[-–—]\s*([^-–—]+?)\s*[-–—]',  # Artist - Song - Album
            r'^([^-–—]+?)\s*[-–—]\s*([^-–—]+?)\s*\(',  # Artist - Song (feat.)
            r'^([^-–—]+?)\s*[-–—]\s*([^-–—]+?)\s*\[',  # Artist - Song [Official]
        ]
        
        for pattern in patterns:
            match = re.match(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: return first part before any separator
        parts = re.split(r'[-–—]', title)
        if parts:
            return parts[0].strip()
        
        return "Unknown Artist"
    
    def _remove_duplicates(self, videos: List[Dict]) -> List[Dict]:
        """Remove duplicate videos based on video ID"""
        seen_ids = set()
        unique_videos = []
        
        for video in videos:
            if video["id"] not in seen_ids:
                unique_videos.append(video)
                seen_ids.add(video["id"])
        
        return unique_videos
    
    def get_variety_stats(self) -> Dict:
        """Get statistics about the variety of music sources"""
        return {
            "total_categories": len(self.global_music_categories),
            "total_regions": len(self.trending_keywords),
            "cultural_variety": len(self.global_music_categories),
            "mood_variety": 8,  # Number of mood categories
            "source": "youtube_music"
        } 