import requests
import time
import random
from typing import Dict, List, Optional
import os

class DeezerService:
    """Deezer API service for global music discovery and variety"""
    
    def __init__(self):
        self.base_url = "https://api.deezer.com"
        self.headers = {"Accept": "application/json"}
        
        # Global music genres for variety
        self.global_genres = {
            "korean": [131, 464, 466],  # K-pop, Korean Pop, Korean Hip-Hop
            "japanese": [132, 467, 468],  # J-Pop, Japanese Pop, Anime
            "indian": [133, 469, 470],  # Bollywood, Indian Pop, Punjabi
            "latin": [98, 471, 472],  # Latin, Reggaeton, Salsa
            "african": [116, 473, 474],  # African, Afrobeats, Nigerian
            "arabic": [134, 475, 476],  # Arabic, Middle Eastern, Turkish
            "chinese": [135, 477, 478],  # Chinese, Mandopop, Cantopop
            "thai": [136, 479, 480],  # Thai, Thai Pop, Luk Thung
            "vietnamese": [137, 481, 482],  # Vietnamese, V-Pop
            "filipino": [138, 483, 484]  # Filipino, OPM, Tagalog
        }
        
        # Mood-based genres
        self.mood_genres = {
            "happy": [106, 107, 108],  # Pop, Rock, Electronic
            "sad": [109, 110, 111],  # Alternative, Indie, Folk
            "energetic": [113, 114, 115],  # Dance, Electronic, Hip-Hop
            "calm": [112, 116, 117],  # Ambient, Chill, Classical
            "romantic": [118, 119, 120],  # R&B, Soul, Jazz
            "party": [113, 114, 121],  # Dance, Electronic, Funk
            "motivational": [122, 123, 124],  # Rock, Metal, Punk
            "nostalgic": [125, 126, 127]  # Retro, Vintage, Oldies
        }
    
    def search_artists(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for artists on Deezer"""
        try:
            params = {
                "q": query,
                "type": "artist",
                "limit": limit
            }
            
            response = requests.get(f"{self.base_url}/search", params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                artists = []
                
                for artist in data.get("data", []):
                    artist_info = {
                        "id": artist.get("id", ""),
                        "name": artist.get("name", ""),
                        "picture": artist.get("picture", ""),
                        "picture_small": artist.get("picture_small", ""),
                        "picture_medium": artist.get("picture_medium", ""),
                        "picture_big": artist.get("picture_big", ""),
                        "picture_xl": artist.get("picture_xl", ""),
                        "tracklist": artist.get("tracklist", ""),
                        "type": artist.get("type", ""),
                        "source": "deezer"
                    }
                    artists.append(artist_info)
                
                return artists
            else:
                print(f"Deezer API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Deezer search error: {e}")
            return []
    
    def get_artists_by_genre(self, genre_id: int, limit: int = 15) -> List[Dict]:
        """Get artists by genre ID"""
        try:
            response = requests.get(f"{self.base_url}/genre/{genre_id}/artists", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                artists = []
                
                for artist in data.get("data", [])[:limit]:
                    artist_info = {
                        "id": artist.get("id", ""),
                        "name": artist.get("name", ""),
                        "picture": artist.get("picture", ""),
                        "picture_small": artist.get("picture_small", ""),
                        "picture_medium": artist.get("picture_medium", ""),
                        "picture_big": artist.get("picture_big", ""),
                        "picture_xl": artist.get("picture_xl", ""),
                        "tracklist": artist.get("tracklist", ""),
                        "type": artist.get("type", ""),
                        "genre_id": genre_id,
                        "source": "deezer"
                    }
                    artists.append(artist_info)
                
                return artists
            else:
                print(f"Deezer genre error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Deezer genre error: {e}")
            return []
    
    def get_global_music_variety(self, category: str = None, limit: int = 20) -> List[Dict]:
        """Get diverse global music from different regions and categories"""
        try:
            all_artists = []
            
            if category and category in self.global_genres:
                # Get artists from specific category
                genre_ids = self.global_genres[category]
                for genre_id in genre_ids[:3]:
                    artists = self.get_artists_by_genre(genre_id, limit // 3)
                    all_artists.extend(artists)
                    time.sleep(0.5)  # Rate limiting
            else:
                # Get diverse artists from multiple categories
                categories = list(self.global_genres.keys())
                random.shuffle(categories)
                
                for cat in categories[:6]:  # Use 6 random categories
                    genre_ids = self.global_genres[cat]
                    genre_id = random.choice(genre_ids)
                    artists = self.get_artists_by_genre(genre_id, limit // 6)
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
            genre_ids = self.mood_genres.get(mood.lower(), [])
            all_artists = []
            
            for genre_id in genre_ids:
                artists = self.get_artists_by_genre(genre_id, limit // len(genre_ids))
                all_artists.extend(artists)
                time.sleep(0.5)
            
            unique_artists = self._remove_duplicates(all_artists)
            random.shuffle(unique_artists)
            
            return unique_artists[:limit]
            
        except Exception as e:
            print(f"Mood music error: {e}")
            return []
    
    def get_artist_details(self, artist_id: int) -> Optional[Dict]:
        """Get detailed artist information"""
        try:
            response = requests.get(f"{self.base_url}/artist/{artist_id}", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                artist = response.json()
                return {
                    "id": artist.get("id", ""),
                    "name": artist.get("name", ""),
                    "link": artist.get("link", ""),
                    "share": artist.get("share", ""),
                    "picture": artist.get("picture", ""),
                    "picture_small": artist.get("picture_small", ""),
                    "picture_medium": artist.get("picture_medium", ""),
                    "picture_big": artist.get("picture_big", ""),
                    "picture_xl": artist.get("picture_xl", ""),
                    "nb_album": artist.get("nb_album", 0),
                    "nb_fan": artist.get("nb_fan", 0),
                    "radio": artist.get("radio", False),
                    "tracklist": artist.get("tracklist", ""),
                    "type": artist.get("type", ""),
                    "source": "deezer"
                }
            else:
                print(f"Deezer artist details error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Artist details error: {e}")
            return None
    
    def get_artist_top_tracks(self, artist_id: int, limit: int = 10) -> List[Dict]:
        """Get top tracks by artist"""
        try:
            response = requests.get(f"{self.base_url}/artist/{artist_id}/top", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tracks = []
                
                for track in data.get("data", [])[:limit]:
                    track_info = {
                        "id": track.get("id", ""),
                        "title": track.get("title", ""),
                        "title_short": track.get("title_short", ""),
                        "title_version": track.get("title_version", ""),
                        "link": track.get("link", ""),
                        "duration": track.get("duration", 0),
                        "rank": track.get("rank", 0),
                        "explicit_lyrics": track.get("explicit_lyrics", False),
                        "explicit_content_lyrics": track.get("explicit_content_lyrics", 0),
                        "explicit_content_cover": track.get("explicit_content_cover", 0),
                        "preview": track.get("preview", ""),
                        "md5_image": track.get("md5_image", ""),
                        "artist": track.get("artist", {}),
                        "album": track.get("album", {}),
                        "type": track.get("type", ""),
                        "source": "deezer"
                    }
                    tracks.append(track_info)
                
                return tracks
            else:
                print(f"Deezer top tracks error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Top tracks error: {e}")
            return []
    
    def get_chart_top_artists(self, limit: int = 20) -> List[Dict]:
        """Get chart top artists globally"""
        try:
            response = requests.get(f"{self.base_url}/chart/0/artists", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                artists = []
                
                for artist in data.get("data", [])[:limit]:
                    artist_info = {
                        "id": artist.get("id", ""),
                        "name": artist.get("name", ""),
                        "picture": artist.get("picture", ""),
                        "picture_small": artist.get("picture_small", ""),
                        "picture_medium": artist.get("picture_medium", ""),
                        "picture_big": artist.get("picture_big", ""),
                        "picture_xl": artist.get("picture_xl", ""),
                        "tracklist": artist.get("tracklist", ""),
                        "type": artist.get("type", ""),
                        "position": len(artists) + 1,
                        "source": "deezer"
                    }
                    artists.append(artist_info)
                
                return artists
            else:
                print(f"Deezer chart error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Chart error: {e}")
            return []
    
    def get_playlist_tracks(self, playlist_id: int, limit: int = 20) -> List[Dict]:
        """Get tracks from a playlist"""
        try:
            response = requests.get(f"{self.base_url}/playlist/{playlist_id}", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tracks = []
                
                for track in data.get("tracks", {}).get("data", [])[:limit]:
                    track_info = {
                        "id": track.get("id", ""),
                        "title": track.get("title", ""),
                        "title_short": track.get("title_short", ""),
                        "title_version": track.get("title_version", ""),
                        "link": track.get("link", ""),
                        "duration": track.get("duration", 0),
                        "rank": track.get("rank", 0),
                        "explicit_lyrics": track.get("explicit_lyrics", False),
                        "explicit_content_lyrics": track.get("explicit_content_lyrics", 0),
                        "explicit_content_cover": track.get("explicit_content_cover", 0),
                        "preview": track.get("preview", ""),
                        "md5_image": track.get("md5_image", ""),
                        "artist": track.get("artist", {}),
                        "album": track.get("album", {}),
                        "type": track.get("type", ""),
                        "source": "deezer"
                    }
                    tracks.append(track_info)
                
                return tracks
            else:
                print(f"Deezer playlist error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Playlist tracks error: {e}")
            return []
    
    def search_playlists(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for playlists"""
        try:
            params = {
                "q": query,
                "type": "playlist",
                "limit": limit
            }
            
            response = requests.get(f"{self.base_url}/search", params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                playlists = []
                
                for playlist in data.get("data", []):
                    playlist_info = {
                        "id": playlist.get("id", ""),
                        "title": playlist.get("title", ""),
                        "description": playlist.get("description", ""),
                        "duration": playlist.get("duration", 0),
                        "public": playlist.get("public", False),
                        "is_loved_track": playlist.get("is_loved_track", False),
                        "collaborative": playlist.get("collaborative", False),
                        "nb_tracks": playlist.get("nb_tracks", 0),
                        "fans": playlist.get("fans", 0),
                        "link": playlist.get("link", ""),
                        "share": playlist.get("share", ""),
                        "picture": playlist.get("picture", ""),
                        "picture_small": playlist.get("picture_small", ""),
                        "picture_medium": playlist.get("picture_medium", ""),
                        "picture_big": playlist.get("picture_big", ""),
                        "picture_xl": playlist.get("picture_xl", ""),
                        "checksum": playlist.get("checksum", ""),
                        "tracklist": playlist.get("tracklist", ""),
                        "creation_date": playlist.get("creation_date", ""),
                        "md5_image": playlist.get("md5_image", ""),
                        "picture_type": playlist.get("picture_type", ""),
                        "creator": playlist.get("creator", {}),
                        "type": playlist.get("type", ""),
                        "source": "deezer"
                    }
                    playlists.append(playlist_info)
                
                return playlists
            else:
                print(f"Deezer playlist search error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Playlist search error: {e}")
            return []
    
    def _remove_duplicates(self, artists: List[Dict]) -> List[Dict]:
        """Remove duplicate artists based on ID"""
        seen_ids = set()
        unique_artists = []
        
        for artist in artists:
            artist_id = artist.get("id")
            if artist_id and artist_id not in seen_ids:
                unique_artists.append(artist)
                seen_ids.add(artist_id)
        
        return unique_artists
    
    def get_variety_stats(self) -> Dict:
        """Get statistics about the variety of music sources"""
        return {
            "total_categories": len(self.global_genres),
            "total_moods": len(self.mood_genres),
            "cultural_variety": len(self.global_genres),
            "mood_variety": len(self.mood_genres),
            "source": "deezer"
        } 