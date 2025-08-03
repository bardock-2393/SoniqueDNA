import requests
import time
from typing import Dict, List, Optional
import os
import urllib.parse
import hashlib

class QlooService:
    """Optimized Qloo API service with minimal overhead"""
    
    def __init__(self):
        self.api_key = os.getenv('QLOO_API_KEY')
        self.base_url = "https://hackathon.api.qloo.com/v2"
        self.headers = {"X-API-Key": self.api_key}
        # Track recently recommended artists to avoid repetition
        self.recent_artists = set()
        self.max_recent_artists = 50  # Reduced from 100 to 50 to prevent over-filtering
    
    def get_tag_ids_fast(self, tags: List[str], domain: str = None) -> List[str]:
        """Get tag IDs efficiently - search Qloo database for existing tags (no limit)"""
        tag_ids = []
        successful_tags = []
        
        print(f"Searching Qloo database for {len(tags)} tags (no limit)...")
        
        # Fallback tags that are known to work
        fallback_tags = {
            "movie": ["drama", "romantic", "action", "comedy", "family"],
            "tv_show": ["drama", "romantic", "comedy", "family", "reality"],
            "podcast": ["entertainment", "interviews", "music", "cultural", "lifestyle"],
            "book": ["romance", "drama", "fiction", "cultural", "contemporary"],
            "artist": ["pop", "mainstream", "indian", "cultural", "contemporary"]
        }
        
        # Try original tags first
        for tag in tags:
            try:
                # Search for the tag in Qloo's database
                url = f"{self.base_url}/tags"
                params = {
                    "filter.query": tag,
                    "limit": 3,  # Get fewer results to find best match
                    "sort": "relevance"  # Sort by relevance, not popularity
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", {}).get("tags", [])
                    
                    if results:
                        # Find the most relevant tag (not necessarily most popular)
                        best_tag = None
                        for result in results:
                            tag_id = result.get("id", "")
                            tag_name = result.get("name", "").lower()
                            tag_type = result.get("type", "")
                            
                            # Check if this is a relevant tag type for the domain
                            if any(category in tag_type.lower() for category in [
                                'music', 'genre', 'style', 'audience', 'character', 
                                'theme', 'plot', 'subgenre', 'mood', 'emotion'
                            ]):
                                best_tag = result
                                break
                        
                        # If no specific relevant tag found, use the first result
                        if not best_tag and results:
                            best_tag = results[0]
                        
                        if best_tag:
                            tag_ids.append(best_tag["id"])
                            successful_tags.append(tag)
                            print(f"✓ '{tag}' → {best_tag['name']} ({best_tag['id']})")
                        else:
                            print(f"✗ '{tag}' - no relevant tags found")
                    else:
                        print(f"✗ '{tag}' - not found in Qloo database")
                else:
                    print(f"✗ '{tag}' - API error: {response.status_code}")
                
                time.sleep(0.05)  # 50ms delay between requests
                
            except Exception as e:
                print(f"Error searching for tag '{tag}': {e}")
                continue
        
        # If we didn't find enough tags, try fallback tags
        if len(tag_ids) < 4:
            print(f"Only found {len(tag_ids)} tags, trying fallback tags...")
            
            # Use provided domain or determine from tags
            if not domain:
                domain = "artist"  # default
                if any(tag in ["drama", "romantic", "action", "comedy", "family"] for tag in tags):
                    domain = "movie"
                elif any(tag in ["entertainment", "interviews", "music"] for tag in tags):
                    domain = "podcast"
                elif any(tag in ["romance", "fiction", "literary"] for tag in tags):
                    domain = "book"
            
            print(f"Using fallback tags for domain: {domain}")
            fallback_list = fallback_tags.get(domain, ["drama", "romantic", "cultural", "entertainment", "contemporary"])
            
            for fallback_tag in fallback_list:
                # No limit - use all fallback tags if needed
                pass
                    
                try:
                    url = f"{self.base_url}/tags"
                    params = {
                        "filter.query": fallback_tag,
                        "limit": 2,
                        "sort": "relevance"
                    }
                    
                    response = requests.get(url, headers=self.headers, params=params, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("results", {}).get("tags", [])
                        
                        if results:
                            best_tag = results[0]
                            tag_ids.append(best_tag["id"])
                            successful_tags.append(fallback_tag)
                            print(f"✓ Fallback '{fallback_tag}' → {best_tag['name']} ({best_tag['id']})")
                    
                    time.sleep(0.05)
                    
                except Exception as e:
                    print(f"Error searching for fallback tag '{fallback_tag}': {e}")
                    continue
        
        print(f"Successfully found {len(successful_tags)}/{len(tags)} tags in Qloo database")
        print(f"Successful tags: {successful_tags}")
        return tag_ids
    
    def get_recommendations_fast(self, tag_ids: List[str], limit: int = 15) -> List[Dict]:
        """Get recommendations efficiently - try each tag individually"""
        if not tag_ids:
            print("No tag IDs provided for recommendations")
            return []
        
        all_recommendations = []
        
        # Try each tag individually
        for i, tag_id in enumerate(tag_ids):
            try:
                url = f"{self.base_url}/insights"
                params = {
                    "filter.type": "urn:entity:artist",
                    "filter.tags": tag_id,  # Single tag
                    "limit": limit // 2,
                    "sort": "relevance"
                }
                
                print(f"Fast recommendations - Tag {i+1}/{len(tag_ids)}: {tag_id}")
                
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Response keys: {list(data.keys())}")
                    
                    # Try different response structures
                    entities = []
                    if "entities" in data:
                        entities = data["entities"]
                    elif "results" in data and "entities" in data["results"]:
                        entities = data["results"]["entities"]
                    elif "data" in data and "entities" in data["data"]:
                        entities = data["data"]["entities"]
                    
                    print(f"✓ Got {len(entities)} recommendations for tag '{tag_id}'")
                    
                    for entity in entities:
                        recommendation = {
                            "id": entity.get("id"),
                            "name": entity.get("name"),
                            "type": entity.get("type"),
                            "popularity": entity.get("popularity", 0),
                            "source_tag": tag_id
                        }
                        all_recommendations.append(recommendation)
                else:
                    print(f"✗ Tag '{tag_id}': Error {response.status_code}")
                    print(f"Response: {response.text[:200]}...")
                
                time.sleep(0.1)  # Small delay
                
            except Exception as e:
                print(f"Error with tag '{tag_id}': {e}")
                continue
        
        # Remove duplicates
        seen_artists = set()
        unique_recommendations = []
        for rec in all_recommendations:
            artist_id = rec.get("id")
            if artist_id and artist_id not in seen_artists:
                unique_recommendations.append(rec)
                seen_artists.add(artist_id)
        
        # Sort by popularity
        unique_recommendations.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        final_recommendations = unique_recommendations[:limit]
        
        print(f"✓ Total unique recommendations: {len(final_recommendations)}")
        return final_recommendations
    
    def get_cross_domain_recommendations(self, tag_ids: List[str], domain: str, limit: int = 10, location: str = None, location_radius: int = 50000) -> List[Dict]:
        """Get cross-domain recommendations efficiently with enhanced data and location support"""
        if not tag_ids:
            print(f"No tag IDs provided for domain: {domain}")
            return []
        
        # Map domain names to correct Qloo entity types
        domain_type_mapping = {
            "movie": "movie",
            "tv_show": "tv_show", 
            "podcast": "podcast",
            "book": "book",
            "artist": "artist"
        }
        
        entity_type = domain_type_mapping.get(domain, domain)
        
        try:
            # Use the correct endpoint and parameters like the old backend
            url = f"{self.base_url}/insights"
            params = {
                "filter.type": f"urn:entity:{entity_type}",
                "filter.tags": ",".join(tag_ids),
                "filter.popularity.min": 0.01,  # Even lower threshold to get more diverse results
                "limit": max(limit * 10, 100),  # Get much more to ensure we have enough recommendations
                "sort": "relevance"  # Sort by relevance, not popularity
            }
            
            print(f"Qloo API request for {domain}:")
            print(f"  URL: {url}")
            print(f"  Entity type: urn:entity:{entity_type}")
            print(f"  Tag IDs: {tag_ids}")
            print(f"  Limit: {max(limit * 6, 60)}")
            
            # Add location-based signals if provided
            if location:
                params["signal.location.query"] = location
                params["signal.location.radius"] = location_radius
                print(f"[QLOO LOCATION] Using location-based recommendations for: {location} (radius: {location_radius}m)")
                print(f"[QLOO LOCATION] Location parameters added to API request")
                print(f"[QLOO LOCATION] Full params with location: {params}")
            else:
                print(f"[QLOO LOCATION] No location provided - using global recommendations")
                print(f"[QLOO LOCATION] Full params without location: {params}")
            
            print(f"Requesting {domain} recommendations with tags: {tag_ids[:3]}...")
            print(f"Using entity type: urn:entity:{entity_type}")
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                entities = data.get("results", {}).get("entities", [])  # Use correct path
                print(f"Received {len(entities)} entities for domain: {domain}")
                print(f"Response data keys: {list(data.keys())}")
                if "results" in data:
                    print(f"Results keys: {list(data['results'].keys())}")
                if entities:
                    print(f"First entity sample: [Entity data truncated]")
                    # Debug: Check if entities have location-related data
                    if location:
                        print(f"[QLOO LOCATION] Checking if entities have location data...")
                        location_entities = 0
                        for entity in entities[:5]:  # Check first 5 entities
                            if entity.get('properties', {}).get('country') or entity.get('properties', {}).get('location'):
                                location_entities += 1
                                print(f"[QLOO LOCATION] Entity '{entity.get('name', 'Unknown')}' has location data: {entity.get('properties', {}).get('country', 'N/A')}")
                        print(f"[QLOO LOCATION] Found {location_entities}/5 entities with location data")
                
                recommendations = []
                # Enhanced randomization for better variety
                import random
                import time
                
                # Use more sophisticated randomization
                random.seed(int(time.time() * 1000000) % 1000000)  # More granular seed
                
                # Get more entities to work with for better variety
                max_entities = min(len(entities), limit * 10)  # Get up to 10x more entities
                shuffled_entities = entities.copy()
                random.shuffle(shuffled_entities)
                
                # Prioritize most relevant tag when we have 5 tags
                if len(tag_ids) >= 5:
                    # Use the first (most relevant) tag for primary sorting
                    primary_tag = tag_ids[0]
                    print(f"[SORTING DEBUG] Using primary tag for sorting: {primary_tag}")
                    
                    # Sort entities by relevance to the primary tag
                    def calculate_primary_tag_relevance(entity):
                        entity_tags = entity.get('tags', [])
                        # Check if primary tag is in entity tags
                        for tag in entity_tags:
                            if isinstance(tag, str) and primary_tag.lower() in tag.lower():
                                return 1.0
                            elif isinstance(tag, dict) and 'name' in tag and primary_tag.lower() in tag['name'].lower():
                                return 1.0
                            elif isinstance(tag, dict) and 'tag' in tag and primary_tag.lower() in tag['tag'].lower():
                                return 1.0
                        return 0.0
                    
                    # Sort by primary tag relevance first, then by popularity
                    sorted_by_primary_tag = sorted(shuffled_entities, 
                                                 key=lambda x: (calculate_primary_tag_relevance(x), x.get('popularity', 0)), 
                                                 reverse=True)
                    selected_entities = sorted_by_primary_tag[:max_entities]
                    
                else:
                    # Use different selection strategies for variety when we have fewer tags
                    selection_strategy = random.choice(['random', 'popularity', 'relevance', 'diversity'])
                    
                    if selection_strategy == 'random':
                        # Pure random selection
                        selected_entities = shuffled_entities[:max_entities]
                    elif selection_strategy == 'popularity':
                        # Sort by popularity and take from different popularity ranges
                        sorted_by_popularity = sorted(shuffled_entities, key=lambda x: x.get('popularity', 0), reverse=True)
                        # Take from high, medium, and low popularity ranges
                        high_pop = sorted_by_popularity[:max_entities//3]
                        medium_pop = sorted_by_popularity[max_entities//3:2*max_entities//3]
                        low_pop = sorted_by_popularity[2*max_entities//3:]
                        selected_entities = random.sample(high_pop, min(len(high_pop), limit//3)) + \
                                          random.sample(medium_pop, min(len(medium_pop), limit//3)) + \
                                          random.sample(low_pop, min(len(low_pop), limit//3))
                    elif selection_strategy == 'relevance':
                        # Sort by relevance (affinity score) and take diverse range
                        sorted_by_relevance = sorted(shuffled_entities, key=lambda x: x.get('affinity_score', 0), reverse=True)
                        selected_entities = sorted_by_relevance[:max_entities]
                    else:  # diversity
                        # Try to maximize diversity by avoiding similar items
                        selected_entities = []
                        used_tags = set()
                        for entity in shuffled_entities[:max_entities]:
                            # Ensure tags are strings, not dictionaries
                            raw_tags = entity.get('tags', [])
                            entity_tags = set()
                            for tag in raw_tags:
                                if isinstance(tag, str):
                                    entity_tags.add(tag)
                                elif isinstance(tag, dict) and 'name' in tag:
                                    entity_tags.add(tag['name'])
                                elif isinstance(tag, dict) and 'tag' in tag:
                                    entity_tags.add(tag['tag'])
                            # If entity has different tags, include it
                            if not entity_tags.intersection(used_tags) or random.random() < 0.3:
                                selected_entities.append(entity)
                                used_tags.update(entity_tags)
                            if len(selected_entities) >= limit * 3:
                                break
                
                # Shuffle again for final variety
                random.shuffle(selected_entities)
                
                for entity in selected_entities[:limit * 3]:  # Process more entities to get enough recommendations
                    # Extract properties based on domain type
                    properties = entity.get("properties", {})
                    
                    # Clean tags to ensure they are strings
                    raw_tags = entity.get("tags", [])
                    clean_tags = []
                    for tag in raw_tags:
                        if isinstance(tag, str):
                            clean_tags.append(tag)
                        elif isinstance(tag, dict) and 'name' in tag:
                            clean_tags.append(tag['name'])
                        elif isinstance(tag, dict) and 'tag' in tag:
                            clean_tags.append(tag['tag'])
                    
                    # Debug: Log image data for troubleshooting
                    image_url = properties.get("image", {}).get("url") if properties.get("image") else None
                    if image_url:
                        print(f"[DEBUG] Found image URL for {entity.get('name')}: {image_url}")
                    else:
                        print(f"[DEBUG] No image URL found for {entity.get('name')}")
                    
                    recommendation = {
                        "id": entity.get("id"),
                        "name": entity.get("name"),
                        "type": entity.get("type"),
                        "popularity": entity.get("popularity", 0),
                        "affinity_score": round(entity.get("popularity", 0) * 0.8, 2),
                        "cultural_relevance": entity.get("cultural_relevance", 0),
                        "tags": clean_tags,
                        "location_based": location is not None,
                        "location": location if location else None,
                        "properties": {
                            "image": {"url": image_url} if image_url else None,
                            "description": properties.get("description"),
                            "url": properties.get("url"),
                            "external_urls": properties.get("external_urls", {})
                        }
                    }
                    
                    # Domain-specific properties
                    if domain == "movie":
                        recommendation["properties"].update({
                            "year": properties.get("year"),
                            "genre": properties.get("genre"),
                            "director": properties.get("director"),
                            "runtime": properties.get("runtime"),
                            "rating": properties.get("rating")
                        })
                    elif domain == "book":
                        recommendation["properties"].update({
                            "author": properties.get("author"),
                            "publisher": properties.get("publisher"),
                            "year": properties.get("year"),
                            "genre": properties.get("genre"),
                            "language": properties.get("language")
                        })
                    elif domain == "podcast":
                        recommendation["properties"].update({
                            "host": properties.get("host"),
                            "episodes": properties.get("episodes"),
                            "genre": properties.get("genre"),
                            "language": properties.get("language")
                        })
                    elif domain == "tv_show":
                        recommendation["properties"].update({
                            "year": properties.get("year"),
                            "genre": properties.get("genre"),
                            "seasons": properties.get("seasons"),
                            "episodes": properties.get("episodes"),
                            "rating": properties.get("rating")
                        })
                    elif domain == "artist":
                        recommendation["properties"].update({
                            "followers": properties.get("followers"),
                            "albums": properties.get("albums"),
                            "genres": properties.get("genres", []),
                            "spotify_url": properties.get("spotify_url")
                        })
                    
                    recommendations.append(recommendation)
                
                # Ensure we return at least the requested number of recommendations
                final_recommendations = recommendations[:limit]
                print(f"Processed {len(final_recommendations)} recommendations for domain: {domain}")
                return final_recommendations
            else:
                print(f"Qloo API error for domain {domain}: {response.status_code}")
                print(f"Response content: [JSON response truncated]")
            
        except Exception as e:
            print(f"Cross-domain recommendations error for {domain}: {e}")
        
        return []
    
    def search_entity(self, query: str, entity_type: str = "artist") -> Optional[Dict]:
        """Search for entity - single API call"""
        try:
            url = f"{self.base_url}/search"
            params = {
                "query": query,
                "filter.type": f"urn:entity:{entity_type}",
                "limit": 1
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                entities = data.get("results", {}).get("entities", [])
                if entities:
                    return entities[0]
            
        except Exception as e:
            print(f"Entity search error: {e}")
        
        return None
    
    def search_artists_by_name(self, artist_names: List[str]) -> List[str]:
        """Search for Qloo artist IDs by name"""
        qloo_artist_ids = []
        
        for artist_name in artist_names[:5]:  # Limit to 5 artists
            try:
                # URL encode the artist name
                encoded_name = urllib.parse.quote(artist_name)
                
                url = f"{self.base_url}/search"
                params = {
                    "query": artist_name,  # Use original name, not encoded
                    "types": ["artist"],
                    "take": 3,
                    "sort_by": "match"
                }
                
                print(f"Searching for artist: {artist_name} (encoded: {encoded_name})")
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if results:
                        qloo_id = results[0].get("id")
                        if qloo_id:
                            qloo_artist_ids.append(qloo_id)
                            print(f"✓ Found '{artist_name}' → {qloo_id}")
                        else:
                            print(f"✗ No ID for '{artist_name}'")
                    else:
                        print(f"✗ No results for '{artist_name}'")
                else:
                    print(f"✗ Search error for '{artist_name}': {response.status_code}")
                    print(f"Response: {response.text[:200]}...")
                
                time.sleep(0.1)  # Small delay
                
            except Exception as e:
                print(f"Error searching for '{artist_name}': {e}")
                continue
        
        return qloo_artist_ids
    
    def get_artist_recommendations_by_tags(self, tag_ids: List[str], artist_ids: List[str] = None, limit: int = 15) -> List[Dict]:
        """Get artist recommendations using tags and artist signals"""
        if not tag_ids:
            return []
        
        all_recommendations = []
        
        # Step 1: Get artist signals if provided
        qloo_artist_signals = []
        if artist_ids:
            # Use known artists that should exist in Qloo
            known_artists = ["Arijit Singh", "Neha Kakkar", "Badshah", "Diljit Dosanjh", "The Weeknd"]
            qloo_artist_signals = self.search_artists_by_name(known_artists)
            print(f"Found {len(qloo_artist_signals)} artist signals for recommendations")
        
        # Step 2: Get recommendations with artist signals
        for i, tag_id in enumerate(tag_ids):
            try:
                url = f"{self.base_url}/insights"
                params = {
                    "filter.type": "urn:entity:artist",
                    "filter.tags": tag_id,
                    "limit": limit // 2,
                    "sort": "relevance"
                }
                
                # Add artist signals if available
                if qloo_artist_signals:
                    artist_signals = [f"urn:entity:artist:{artist_id}" for artist_id in qloo_artist_signals[:3]]
                    params["signal.interests.entities"] = ",".join(artist_signals)
                    print(f"Using {len(artist_signals)} artist signals")
                
                print(f"Artist recommendations - Tag {i+1}/{len(tag_ids)}: {tag_id}")
                
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    entities = data.get("results", {}).get("entities", [])
                
                    print(f"✓ Got {len(entities)} artists for tag '{tag_id}'")
                    
                    for entity in entities:
                        recommendation = {
                            "id": entity.get("id"),
                            "name": entity.get("name"),
                            "popularity": entity.get("popularity", 0),
                            "type": entity.get("type"),
                            "affinity_score": round(entity.get("popularity", 0) * 0.8, 2),
                            "source_tag": tag_id
                        }
                        all_recommendations.append(recommendation)
                else:
                    print(f"✗ Tag '{tag_id}': Error {response.status_code}")
                
                time.sleep(0.1)
            
            except Exception as e:
                print(f"Error with tag '{tag_id}': {e}")
                continue
        
        # Remove duplicates
        seen_artists = set()
        unique_recommendations = []
        for rec in all_recommendations:
            artist_id = rec.get("id")
            if artist_id and artist_id not in seen_artists:
                unique_recommendations.append(rec)
                seen_artists.add(artist_id)
        
        unique_recommendations.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        final_recommendations = unique_recommendations[:limit]
        
        print(f"✓ Total unique artist recommendations: {len(final_recommendations)}")
        return final_recommendations
    
    def get_fallback_tag_ids(self, domain: str) -> List[str]:
        """Get fallback tag IDs for when primary tag search fails"""
        # Known working tag IDs from Qloo database
        fallback_tag_ids = {
            "music": [
                "urn:tag:pop",  # Pop music
                "urn:tag:mainstream",  # Mainstream
                "urn:tag:indian",  # Indian music
                "urn:tag:cultural",  # Cultural
                "urn:tag:contemporary"  # Contemporary
            ],
            "movie": [
                "urn:tag:drama",  # Drama
                "urn:tag:romantic",  # Romantic
                "urn:tag:action",  # Action
                "urn:tag:comedy",  # Comedy
                "urn:tag:family"  # Family
            ],
            "book": [
                "urn:tag:romance",  # Romance
                "urn:tag:drama",  # Drama
                "urn:tag:fiction",  # Fiction
                "urn:tag:cultural",  # Cultural
                "urn:tag:contemporary"  # Contemporary
            ],
            "podcast": [
                "urn:tag:entertainment",  # Entertainment
                "urn:tag:interviews",  # Interviews
                "urn:tag:music",  # Music
                "urn:tag:cultural",  # Cultural
                "urn:tag:lifestyle"  # Lifestyle
            ]
        }
        
        return fallback_tag_ids.get(domain, fallback_tag_ids["music"])
    
    def get_enhanced_recommendations(self, tag_ids: List[str], user_artists: List[Dict] = None, 
                                   user_tracks: List[Dict] = None, location: str = None, 
                                   location_radius: int = 5000000, cultural_context: Dict = None, 
                                   limit: int = 15) -> List[Dict]:
        """Get enhanced recommendations with cultural intelligence and user signals"""
        try:
            if not tag_ids:
                print("No tag IDs provided for enhanced recommendations")
                return []
            
            print(f"Getting enhanced recommendations with {len(tag_ids)} tag IDs: {tag_ids[:3]}")
            if location:
                print(f"📍 Location-aware recommendations for: {location} (radius: {location_radius}m)")
                print(f"[QLOO LOCATION] Using location-based API call for music recommendations")
            else:
                print(f"[QLOO LOCATION] No location provided - using global recommendations")
            
            # Use location-aware API call if location is provided
            if location:
                recommendations = self.get_music_recommendations_with_user_signals(
                    tag_ids=tag_ids,
                    user_artist_ids=[artist.get('id', '') for artist in (user_artists or []) if isinstance(artist, dict) and artist.get('id')],
                    user_track_ids=[track.get('id', '') for track in (user_tracks or []) if isinstance(track, dict) and track.get('id')],
                    user_country=None,  # We'll use location directly
                    location=location,
                    location_radius=location_radius,
                    limit=limit * 2
                )
            else:
                # Fallback to standard recommendations
                recommendations = self.get_recommendations_fast(tag_ids, limit * 2)
            
            if not recommendations:
                print("Standard recommendations failed, trying fallback approach...")
                # Fallback: try with individual tag IDs
                for tag_id in tag_ids[:3]:
                    try:
                        fallback_recs = self.get_recommendations_fast([tag_id], limit)
                        if fallback_recs:
                            recommendations.extend(fallback_recs)
                            print(f"Got {len(fallback_recs)} recommendations from tag {tag_id}")
                    except Exception as e:
                        print(f"Fallback recommendation failed for tag {tag_id}: {e}")
                        continue
            
            # If still no recommendations, use hardcoded fallback artists
            if not recommendations:
                print("No Qloo recommendations found, using hardcoded fallback artists")
                recommendations = self.get_hardcoded_fallback_artists(cultural_context, limit)
                if recommendations:
                    print(f"✓ Using {len(recommendations)} hardcoded fallback artists")
                else:
                    print("⚠️ Even hardcoded fallback failed, returning empty list")
            
            # Enhance recommendations with cultural context and location awareness
            enhanced_recommendations = []
            for entity in recommendations:
                # Add cultural relevance score
                cultural_relevance = 0.0
                if cultural_context and cultural_context.get("cultural_elements"):
                    cultural_elements = cultural_context["cultural_elements"]
                    entity_name = entity.get("name", "").lower()
                    entity_description = entity.get("description", "").lower()
                    
                    for element in cultural_elements:
                        if element.lower() in entity_name or element.lower() in entity_description:
                            cultural_relevance += 0.3
                
                # Add location relevance score
                location_relevance = 0.0
                if location:
                    entity_name = entity.get("name", "").lower()
                    entity_description = entity.get("description", "").lower()
                    
                    # Check if entity is relevant to the location
                    if location.lower() in entity_name or location.lower() in entity_description:
                        location_relevance = 0.8
                    elif any(loc_word in entity_name for loc_word in ["local", "regional", "native"]):
                        location_relevance = 0.5
                    elif any(loc_word in entity_name for loc_word in ["indian", "bollywood", "hindi", "punjabi", "desi"]):
                        # For Indian locations, give relevance to Indian artists
                        if "mumbai" in location.lower() or "india" in location.lower():
                            location_relevance = 0.4
                    elif any(loc_word in entity_name for loc_word in ["western", "pop", "rock", "hip_hop"]):
                        # For Western locations, give relevance to Western artists
                        if any(western_loc in location.lower() for western_loc in ["new york", "london", "toronto", "sydney", "us", "uk", "canada", "australia"]):
                            location_relevance = 0.4
                
                # Create enhanced entity
                enhanced_entity = {
                    "id": entity.get("id", f"fallback_{len(enhanced_recommendations)}"),
                    "name": entity.get("name", "Unknown Artist"),
                    "type": entity.get("type", "urn:entity:artist"),
                    "popularity": entity.get("popularity", 0.5),
                    "cultural_relevance": min(cultural_relevance, 1.0),
                    "location_relevance": min(location_relevance, 1.0),
                    "description": entity.get("description", ""),
                    "tags": entity.get("tags", [])
                }
                
                enhanced_recommendations.append(enhanced_entity)
            
            # Sort by cultural relevance, location relevance, and popularity
            enhanced_recommendations.sort(key=lambda x: (
                x.get("cultural_relevance", 0) * 0.35 + 
                x.get("location_relevance", 0) * 0.35 + 
                x.get("popularity", 0) * 0.3
            ), reverse=True)
            
            print(f"Returning {len(enhanced_recommendations)} enhanced recommendations")
            return enhanced_recommendations[:limit]
            
        except Exception as e:
            print(f"Error in enhanced recommendations: {e}")
            # Return hardcoded fallback
            return self.get_hardcoded_fallback_artists(cultural_context, limit)
    


    def get_hardcoded_fallback_artists(self, cultural_context: Dict = None, limit: int = 15) -> List[Dict]:
        """Get hardcoded fallback artists when Qloo API fails"""
        try:
            # Determine cultural context for appropriate fallback artists
            region = cultural_context.get("region", "global") if cultural_context else "global"
            language_preference = cultural_context.get("language_preference", "any") if cultural_context else "any"
            
            # Hardcoded artist lists by region and language
            fallback_artists = {
                "south_asia": {
                    "hindi": [
                        {"id": "fallback_1", "name": "Arijit Singh", "type": "urn:entity:artist", "popularity": 0.9, "description": "Popular Hindi playback singer"},
                        {"id": "fallback_2", "name": "Neha Kakkar", "type": "urn:entity:artist", "popularity": 0.8, "description": "Bollywood playback singer"},
                        {"id": "fallback_3", "name": "Badshah", "type": "urn:entity:artist", "popularity": 0.8, "description": "Indian rapper and music producer"},
                        {"id": "fallback_4", "name": "Harrdy Sandhu", "type": "urn:entity:artist", "popularity": 0.7, "description": "Punjabi singer and actor"},
                        {"id": "fallback_5", "name": "Shreya Ghoshal", "type": "urn:entity:artist", "popularity": 0.9, "description": "Classical and playback singer"},
                        {"id": "fallback_6", "name": "Atif Aslam", "type": "urn:entity:artist", "popularity": 0.8, "description": "Pakistani singer and actor"},
                        {"id": "fallback_7", "name": "Pritam", "type": "urn:entity:artist", "popularity": 0.8, "description": "Bollywood music composer"},
                        {"id": "fallback_8", "name": "A.R. Rahman", "type": "urn:entity:artist", "popularity": 0.9, "description": "Oscar-winning music composer"},
                        {"id": "fallback_9", "name": "Diljit Dosanjh", "type": "urn:entity:artist", "popularity": 0.8, "description": "Punjabi singer and actor"},
                        {"id": "fallback_10", "name": "Guru Randhawa", "type": "urn:entity:artist", "popularity": 0.7, "description": "Punjabi singer and songwriter"}
                    ],
                    "any": [
                        {"id": "fallback_11", "name": "The Weeknd", "type": "urn:entity:artist", "popularity": 0.9, "description": "Canadian singer and songwriter"},
                        {"id": "fallback_12", "name": "Ed Sheeran", "type": "urn:entity:artist", "popularity": 0.9, "description": "English singer-songwriter"},
                        {"id": "fallback_13", "name": "Taylor Swift", "type": "urn:entity:artist", "popularity": 0.9, "description": "American singer-songwriter"},
                        {"id": "fallback_14", "name": "Justin Bieber", "type": "urn:entity:artist", "popularity": 0.8, "description": "Canadian pop singer"},
                        {"id": "fallback_15", "name": "Ariana Grande", "type": "urn:entity:artist", "popularity": 0.9, "description": "American singer and actress"}
                    ]
                },
                "western": {
                    "english": [
                        {"id": "fallback_16", "name": "The Weeknd", "type": "urn:entity:artist", "popularity": 0.9, "description": "Canadian singer and songwriter"},
                        {"id": "fallback_17", "name": "Ed Sheeran", "type": "urn:entity:artist", "popularity": 0.9, "description": "English singer-songwriter"},
                        {"id": "fallback_18", "name": "Taylor Swift", "type": "urn:entity:artist", "popularity": 0.9, "description": "American singer-songwriter"},
                        {"id": "fallback_19", "name": "Post Malone", "type": "urn:entity:artist", "popularity": 0.8, "description": "American rapper and singer"},
                        {"id": "fallback_20", "name": "Dua Lipa", "type": "urn:entity:artist", "popularity": 0.8, "description": "English singer and songwriter"},
                        {"id": "fallback_21", "name": "Billie Eilish", "type": "urn:entity:artist", "popularity": 0.8, "description": "American singer and songwriter"},
                        {"id": "fallback_22", "name": "Harry Styles", "type": "urn:entity:artist", "popularity": 0.8, "description": "English singer and actor"},
                        {"id": "fallback_23", "name": "Coldplay", "type": "urn:entity:artist", "popularity": 0.8, "description": "English rock band"},
                        {"id": "fallback_24", "name": "Imagine Dragons", "type": "urn:entity:artist", "popularity": 0.7, "description": "American pop rock band"},
                        {"id": "fallback_25", "name": "Maroon 5", "type": "urn:entity:artist", "popularity": 0.7, "description": "American pop rock band"}
                    ],
                    "any": [
                        {"id": "fallback_26", "name": "Martin Garrix", "type": "urn:entity:artist", "popularity": 0.8, "description": "Dutch DJ and record producer"},
                        {"id": "fallback_27", "name": "The Chainsmokers", "type": "urn:entity:artist", "popularity": 0.7, "description": "American DJ duo"},
                        {"id": "fallback_28", "name": "Calvin Harris", "type": "urn:entity:artist", "popularity": 0.8, "description": "Scottish DJ and record producer"},
                        {"id": "fallback_29", "name": "David Guetta", "type": "urn:entity:artist", "popularity": 0.7, "description": "French DJ and record producer"},
                        {"id": "fallback_30", "name": "Marshmello", "type": "urn:entity:artist", "popularity": 0.7, "description": "American electronic music producer"}
                    ]
                }
            }
            
            # Get appropriate artist list
            if region in fallback_artists:
                if language_preference in fallback_artists[region]:
                    artists = fallback_artists[region][language_preference]
                else:
                    artists = fallback_artists[region]["any"]
            else:
                # Global fallback
                artists = [
                    {"id": "fallback_31", "name": "The Weeknd", "type": "urn:entity:artist", "popularity": 0.9, "description": "Canadian singer and songwriter"},
                    {"id": "fallback_32", "name": "Ed Sheeran", "type": "urn:entity:artist", "popularity": 0.9, "description": "English singer-songwriter"},
                    {"id": "fallback_33", "name": "Arijit Singh", "type": "urn:entity:artist", "popularity": 0.9, "description": "Popular Hindi playback singer"},
                    {"id": "fallback_34", "name": "Taylor Swift", "type": "urn:entity:artist", "popularity": 0.9, "description": "American singer-songwriter"},
                    {"id": "fallback_35", "name": "Post Malone", "type": "urn:entity:artist", "popularity": 0.8, "description": "American rapper and singer"}
                ]
            
            # Add cultural relevance score
            for artist in artists:
                cultural_relevance = 0.0
                if cultural_context and cultural_context.get("cultural_elements"):
                    cultural_elements = cultural_context["cultural_elements"]
                    artist_name = artist.get("name", "").lower()
                    
                    for element in cultural_elements:
                        if element.lower() in artist_name:
                            cultural_relevance += 0.3
                
                artist["cultural_relevance"] = min(cultural_relevance, 1.0)
                artist["tags"] = []
            
            print(f"Using {len(artists)} hardcoded fallback artists for region: {region}, language: {language_preference}")
            return artists[:limit]
            
        except Exception as e:
            print(f"Error getting hardcoded fallback artists: {e}")
            # Ultimate fallback
            return [
                {"id": "fallback_ultimate", "name": "The Weeknd", "type": "urn:entity:artist", "popularity": 0.9, "cultural_relevance": 0.0, "description": "Canadian singer and songwriter", "tags": []}
            ]
    
    def search_artist_by_name(self, artist_name: str) -> Optional[str]:
        """Search for a Qloo artist entity ID by name"""
        try:
            url = f"{self.base_url}/search"
            params = {
                "query": artist_name,
                "types": ["artist"],
                "take": 3,
                "sort_by": "match"
            }
            
            print(f"Searching Qloo for artist: {artist_name}")
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    qloo_id = results[0].get("id")
                    print(f"✓ Found Qloo ID for '{artist_name}': {qloo_id}")
                    return qloo_id
                else:
                    print(f"✗ No Qloo results for '{artist_name}'")
            
            return None
            
        except Exception as e:
            print(f"Error searching for artist '{artist_name}': {e}")
            return None





    def get_music_recommendations_with_user_signals(self, tag_ids: List[str], user_artist_ids: List[str], user_track_ids: List[str], user_country: str = None, location: str = None, location_radius: int = 50000, limit: int = 20) -> List[Dict]:
        """Get unified music recommendations with variety and relevance - prevents same artists"""
        if not tag_ids:
            print(f"No tag IDs provided for music recommendations")
            return []
        
        all_recommendations = []
        
        # Use only music-specific tags for better results
        music_tag_ids = []
        for tag_id in tag_ids:
            if 'music' in tag_id and 'media' not in tag_id:
                music_tag_ids.append(tag_id)
        
        if not music_tag_ids:
            music_tag_ids = tag_ids[:3]  # Fallback to first 3 tags
        
        print(f"[VARIETY STRATEGY] Using {len(music_tag_ids)} music tags: {music_tag_ids[:3]}...")
        
        # Create context-dependent variety seed instead of just time-based
        import time
        import hashlib
        
        # Create a unique seed based on context, tags, and time
        context_string = f"{user_country}_{location}_{','.join(music_tag_ids)}_{int(time.time() / 60)}"  # Change every minute
        variety_seed = int(hashlib.md5(context_string.encode()).hexdigest()[:8], 16) % 10000
        print(f"[VARIETY] Context-dependent variety seed: {variety_seed}")
        print(f"[VARIETY] Context string: {context_string[:50]}...")
        
        # Multiple strategies to get diverse artists with different offsets
        strategies = [
            {"sort": "relevance", "offset": 0},
            {"sort": "relevance", "offset": variety_seed % 20},
            {"sort": "popularity", "offset": variety_seed % 15},
            {"sort": "relevance", "offset": (variety_seed * 2) % 25},
            {"sort": "popularity", "offset": (variety_seed * 3) % 30}
        ]
        
        for strategy_idx, strategy in enumerate(strategies):
            for tag_id in music_tag_ids:
                try:
                    url = f"{self.base_url}/insights"
                    params = {
                        "filter.type": "urn:entity:artist",
                        "filter.tags": tag_id,
                        "limit": max(4, limit // (len(music_tag_ids) * len(strategies))),
                        "sort": strategy["sort"],
                        "offset": strategy["offset"]
                    }
                    
                    # Add location signals if available
                    if location:
                        params["signal.location.query"] = location
                        params["signal.location.radius"] = location_radius
                    
                    # Add cultural signals if available
                    if user_country:
                        cultural_tags = self._get_cultural_tags_for_country(user_country)
                        if cultural_tags:
                            params["filter.tags"] = f"{tag_id},{cultural_tags[0]}"
                    
                    print(f"Strategy {strategy_idx+1} - Tag: {tag_id} (sort: {strategy['sort']}, offset: {strategy['offset']})")
                    response = requests.get(url, headers=self.headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        entities = data.get("results", {}).get("entities", [])
                        
                        for entity in entities:
                            rec = self._format_recommendation(entity, tag_id, f"strategy_{strategy_idx+1}")
                            # Mark relevance based on signals
                            if location:
                                rec["location_relevance"] = True
                            if user_country:
                                rec["cultural_relevance"] = True
                            if user_artist_ids:
                                rec["user_taste_relevance"] = True
                            rec["strategy"] = strategy_idx + 1
                            rec["variety_seed"] = variety_seed
                            rec["context_hash"] = hashlib.md5(context_string.encode()).hexdigest()[:8]
                            all_recommendations.append(rec)
                        
                        print(f"  ✓ Got {len(entities)} artists")
                    else:
                        print(f"  ✗ Error: {response.status_code}")
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error with strategy {strategy_idx+1} tag '{tag_id}': {e}")
                    continue
        
        print(f"Total recommendations collected: {len(all_recommendations)}")
        
        # Remove duplicates and sort by relevance
        unique_recommendations = self._deduplicate_and_sort(all_recommendations)
        
        # Apply relevance scoring with user taste consideration
        scored_recommendations = self._apply_relevance_scoring_with_user_taste(unique_recommendations, user_artist_ids, user_track_ids, user_country, location)
        
        # Add variety to final selection - shuffle and pick diverse artists
        import random
        random.seed(variety_seed)
        
        # Group by strategy to ensure diversity
        strategy_groups = {}
        for rec in scored_recommendations:
            strategy = rec.get("strategy", 1)
            if strategy not in strategy_groups:
                strategy_groups[strategy] = []
            strategy_groups[strategy].append(rec)
        
        # Pick artists from each strategy to ensure variety
        final_recommendations = []
        if len(strategy_groups) > 0:
            artists_per_strategy = max(2, limit // len(strategy_groups))
        else:
            artists_per_strategy = limit  # If no strategy groups, use all available
        
        for strategy, artists in strategy_groups.items():
            # Shuffle artists within each strategy
            random.shuffle(artists)
            final_recommendations.extend(artists[:artists_per_strategy])
        
        # If we don't have enough, add more from the best scored
        if len(final_recommendations) < limit:
            remaining = [rec for rec in scored_recommendations if rec not in final_recommendations]
            random.shuffle(remaining)
            final_recommendations.extend(remaining[:limit - len(final_recommendations)])
        
        # Apply variety filtering to prevent repetition
        final_recommendations = self._add_variety_to_recommendations(final_recommendations, variety_seed)
        final_recommendations = final_recommendations[:limit]
        
        print(f"Final variety recommendations: {len(final_recommendations)}")
        for i, rec in enumerate(final_recommendations[:5]):
            print(f"  {i+1}. {rec['name']} (strategy: {rec.get('strategy', 1)}, relevance: {rec.get('relevance_score', 0):.2f})")
        
        return final_recommendations

    def _get_user_taste_recommendations(self, user_artist_ids: List[str], user_track_ids: List[str], limit: int) -> List[Dict]:
        """Get recommendations based on user's listening history and context"""
        recommendations = []
        
        # Analyze user's actual listening patterns to determine relevant tags
        user_genres = self._analyze_user_genres(user_artist_ids, user_track_ids)
        
        # Use user's actual genres + proven Qloo tags
        music_tags = []
        
        # Add user's preferred genres first (higher priority)
        for genre in user_genres[:3]:  # Top 3 genres
            if genre in ["pop", "rock", "hip_hop", "electronic", "indie", "alternative", "r&b", "soul", "jazz", "classical", "country", "folk", "reggae", "latin", "k-pop", "j-pop", "bollywood", "hindi", "punjabi", "bhangra"]:
                music_tags.append(f"urn:tag:genre:music:{genre}")
        
        # Add proven Qloo tags as fallback
        proven_tags = [
            "urn:tag:genre:music:mainstream",
            "urn:tag:genre:music:bollywood", 
            "urn:tag:genre:music:pop",
            "urn:tag:genre:music:hip_hop",
            "urn:tag:genre:music:electronic",
            "urn:tag:genre:music:rock"
        ]
        
        # Combine user genres with proven tags, avoiding duplicates
        for tag in proven_tags:
            if tag not in music_tags:
                music_tags.append(tag)
        
        print(f"[USER TASTE] User genres: {user_genres}")
        print(f"[USER TASTE] Using tags: {music_tags[:5]}...")
        
        for tag_id in music_tags:
            try:
                url = f"{self.base_url}/insights"
                params = {
                    "filter.type": "urn:entity:artist",
                    "filter.tags": tag_id,
                    "limit": max(8, limit // len(music_tags)),
                    "sort": "relevance"
                }
                
                print(f"User Taste - Tag: {tag_id}")
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    entities = data.get("results", {}).get("entities", [])
                    
                    for entity in entities:
                        rec = self._format_recommendation(entity, tag_id, "user_taste")
                        rec["user_taste_relevance"] = True
                        recommendations.append(rec)
                
                    print(f"  ✓ Got {len(entities)} user taste artists")
                else:
                    print(f"  ✗ Error: {response.status_code}")
            
                time.sleep(0.1)
            
            except Exception as e:
                print(f"Error with user taste tag '{tag_id}': {e}")
                continue
        
        return recommendations

    def _apply_relevance_scoring_with_user_taste(self, recommendations: List[Dict], user_artist_ids: List[str], user_track_ids: List[str], country: str, location: str) -> List[Dict]:
        """Apply relevance scoring with user taste consideration"""
        # Analyze user's preferred genres for better scoring
        user_genres = self._analyze_user_genres(user_artist_ids, user_track_ids)
        
        for rec in recommendations:
            relevance_score = rec.get("popularity", 0)
            
            # Boost user taste relevance (highest priority)
            if rec.get("user_taste_relevance"):
                relevance_score *= 2.0  # Increased from 1.5
                print(f"  🎯 User taste boost for: {rec['name']}")
            
            # Boost artists similar to user's preferred genres
            artist_tags = rec.get("tags", [])
            if isinstance(artist_tags, list):
                artist_genres = [str(tag).lower() for tag in artist_tags if isinstance(tag, str) and "genre" in tag.lower()]
            else:
                artist_genres = []
            
            for user_genre in user_genres:
                if any(user_genre in genre for genre in artist_genres):
                    relevance_score *= 1.4
                    print(f"  🎵 Genre match boost for: {rec['name']} (matches {user_genre})")
                    break
            
            # Boost location relevance (if working)
            if rec.get("location_relevance"):
                relevance_score *= 1.3
            
            # Boost cultural relevance
            if rec.get("cultural_relevance"):
                relevance_score *= 1.2
            
            # Boost high popularity
            if rec.get("high_popularity"):
                relevance_score *= 1.1
            
            # Boost genre diversity
            if rec.get("genre_diversity"):
                relevance_score *= 1.05
            
            # Additional boost for cultural context
            if country == "IN" and any(tag in str(rec.get("tags", [])) for tag in ["bollywood", "indian", "hindi"]):
                relevance_score *= 1.2
                print(f"  🇮🇳 Cultural boost for: {rec['name']}")
            
            rec["relevance_score"] = round(relevance_score, 3)
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return recommendations

    def _get_global_recommendations(self, tag_ids: List[str], limit: int) -> List[Dict]:
        """Get global recommendations without location filtering"""
        recommendations = []
        
        for tag_id in tag_ids:
            try:
                url = f"{self.base_url}/insights"
                params = {
                    "filter.type": "urn:entity:artist",
                    "filter.tags": tag_id,
                    "limit": max(15, limit // len(tag_ids)),
                    "sort": "relevance"
                }
                
                print(f"Global - Tag: {tag_id}")
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    entities = data.get("results", {}).get("entities", [])
                    
                    for entity in entities:
                        rec = self._format_recommendation(entity, tag_id, "global")
                        recommendations.append(rec)
                    
                    print(f"  ✓ Got {len(entities)} artists")
                else:
                    print(f"  ✗ Error: {response.status_code}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error with global tag '{tag_id}': {e}")
                continue
        
        return recommendations

    def _get_location_recommendations(self, tag_ids: List[str], location: str, radius: int, limit: int) -> List[Dict]:
        """Get location-based recommendations"""
        recommendations = []
        
        for tag_id in tag_ids:
            try:
                url = f"{self.base_url}/insights"
                params = {
                    "filter.type": "urn:entity:artist",
                    "filter.tags": tag_id,
                    "signal.location.query": location,
                    "signal.location.radius": radius,  # Keep in meters
                    "limit": max(10, limit // len(tag_ids)),
                    "sort": "relevance"
                }
                
                print(f"Location - Tag: {tag_id}, Location: {location}")
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
                if response.status_code == 200:
                    data = response.json()
                    entities = data.get("results", {}).get("entities", [])
                    
                    for entity in entities:
                        rec = self._format_recommendation(entity, tag_id, "location")
                        rec["location_relevance"] = True
                        recommendations.append(rec)
                    
                    print(f"  ✓ Got {len(entities)} location-based artists")
                else:
                    print(f"  ✗ Error: {response.status_code}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error with location tag '{tag_id}': {e}")
                continue
        
        return recommendations

    def _get_cultural_recommendations(self, tag_ids: List[str], country: str, limit: int) -> List[Dict]:
        """Get cultural context recommendations"""
        recommendations = []
        
        # Add cultural tags based on country
        cultural_tags = self._get_cultural_tags_for_country(country)
        all_tags = tag_ids + cultural_tags
        
        for tag_id in all_tags[:4]:  # Limit to avoid too many requests
            try:
                url = f"{self.base_url}/insights"
                params = {
                    "filter.type": "urn:entity:artist",
                    "filter.tags": tag_id,
                    "limit": max(8, limit // 4),
                    "sort": "relevance"
                }
                
                print(f"Cultural - Tag: {tag_id}, Country: {country}")
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    entities = data.get("results", {}).get("entities", [])
                    
                    for entity in entities:
                        rec = self._format_recommendation(entity, tag_id, "cultural")
                        rec["cultural_relevance"] = True
                        recommendations.append(rec)
                    
                    print(f"  ✓ Got {len(entities)} cultural artists")
                else:
                    print(f"  ✗ Error: {response.status_code}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error with cultural tag '{tag_id}': {e}")
                continue
        
        return recommendations

    def _get_popular_recommendations(self, tag_ids: List[str], limit: int) -> List[Dict]:
        """Get high-popularity recommendations"""
        recommendations = []
        
        for tag_id in tag_ids:
            try:
                url = f"{self.base_url}/insights"
                params = {
                    "filter.type": "urn:entity:artist",
                    "filter.tags": tag_id,
                    "filter.popularity.min": 0.5,  # High popularity threshold
                    "limit": max(8, limit // len(tag_ids)),
                    "sort": "popularity"  # Sort by popularity instead of relevance
                }
                
                print(f"Popular - Tag: {tag_id}")
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    entities = data.get("results", {}).get("entities", [])
                    
                    for entity in entities:
                        rec = self._format_recommendation(entity, tag_id, "popular")
                        rec["high_popularity"] = True
                        recommendations.append(rec)
                    
                    print(f"  ✓ Got {len(entities)} popular artists")
                else:
                    print(f"  ✗ Error: {response.status_code}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error with popular tag '{tag_id}': {e}")
                continue
        
        return recommendations

    def _get_diverse_recommendations(self, tag_ids: List[str], limit: int) -> List[Dict]:
        """Get diverse genre recommendations"""
        recommendations = []
        
        # Use different music genre tags for diversity - focus on tags that work
        diverse_tags = [
            "urn:tag:genre:music:mainstream",
            "urn:tag:genre:music:bollywood", 
            "urn:tag:genre:music:pop",
            "urn:tag:genre:music:hip_hop",
            "urn:tag:genre:music:electronic"
        ]
        
        for tag_id in diverse_tags:
            try:
                url = f"{self.base_url}/insights"
                params = {
                    "filter.type": "urn:entity:artist",
                    "filter.tags": tag_id,
                    "limit": max(6, limit // len(diverse_tags)),
                    "sort": "relevance"
                }
                
                print(f"Diverse - Tag: {tag_id}")
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    entities = data.get("results", {}).get("entities", [])
                    
                    for entity in entities:
                        rec = self._format_recommendation(entity, tag_id, "diverse")
                        rec["genre_diversity"] = True
                        recommendations.append(rec)
                    
                    print(f"  ✓ Got {len(entities)} diverse artists")
                else:
                    print(f"  ✗ Error: {response.status_code}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error with diverse tag '{tag_id}': {e}")
                continue
        
        return recommendations

    def _format_recommendation(self, entity: Dict, source_tag: str, strategy: str) -> Dict:
        """Format entity into recommendation object"""
        properties = entity.get("properties", {})
        entity_id = entity.get("id") or entity.get("name", "unknown")
        
        return {
            "id": entity_id,
            "name": entity.get("name"),
            "type": entity.get("type"),
            "popularity": entity.get("popularity", 0),
            "affinity_score": round(entity.get("popularity", 0) * 0.8, 2),
            "cultural_relevance": entity.get("cultural_relevance", 0),
            "tags": entity.get("tags", []),
            "source_tag": source_tag,
            "source_strategy": strategy,
            "properties": {
                "image": {"url": properties.get("image", {}).get("url")} if properties.get("image") else None,
                "description": properties.get("description"),
                "url": properties.get("url"),
                "external_urls": properties.get("external_urls", {}),
                "followers": properties.get("followers"),
                "albums": properties.get("albums"),
                "genres": properties.get("genres", []),
                "spotify_url": properties.get("spotify_url")
            }
        }
        
    def _deduplicate_and_sort(self, recommendations: List[Dict]) -> List[Dict]:
        """Remove duplicates and sort by popularity"""
        seen_artists = set()
        unique_recommendations = []
        
        for rec in recommendations:
            artist_id = rec.get("id")
            artist_name = rec.get("name", "").lower()
            
            if not artist_id or artist_id == "No ID" or artist_id == "unknown":
                artist_id = artist_name
            
            if artist_id and artist_id not in seen_artists:
                unique_recommendations.append(rec)
                seen_artists.add(artist_id)
        
        # Sort by popularity
        unique_recommendations.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        return unique_recommendations

    def _apply_relevance_scoring(self, recommendations: List[Dict], country: str, location: str) -> List[Dict]:
        """Apply relevance scoring based on context"""
        for rec in recommendations:
            relevance_score = rec.get("popularity", 0)
            
            # Boost location relevance
            if rec.get("location_relevance"):
                relevance_score *= 1.3
            
            # Boost cultural relevance
            if rec.get("cultural_relevance"):
                relevance_score *= 1.2
            
            # Boost high popularity
            if rec.get("high_popularity"):
                relevance_score *= 1.1
            
            # Boost genre diversity
            if rec.get("genre_diversity"):
                relevance_score *= 1.05
            
            rec["relevance_score"] = round(relevance_score, 3)
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return recommendations

    def _analyze_user_genres(self, user_artist_ids: List[str], user_track_ids: List[str]) -> List[str]:
        """Analyze user's listening patterns to extract preferred genres"""
        # This would ideally use Spotify API to get actual genres
        # For now, use a simplified analysis based on common patterns
        
        # Common genre patterns based on popular artists
        genre_patterns = {
            "rock": ["coldplay", "the beatles", "pink floyd", "led zeppelin", "queen", "nirvana", "metallica"],
            "pop": ["taylor swift", "ed sheeren", "justin bieber", "ariana grande", "dua lipa"],
            "hip_hop": ["drake", "kendrick lamar", "j. cole", "travis scott", "post malone"],
            "electronic": ["david guetta", "calvin harris", "skrillex", "deadmau5", "marshmello"],
            "indie": ["arctic monkeys", "the strokes", "vampire weekend", "tame impala"],
            "r&b": ["the weeknd", "bruno mars", "frank ocean", "sza", "daniel caesar"],
            "country": ["luke combs", "morgan wallen", "kane brown", "maren morris"],
            "jazz": ["miles davis", "john coltrane", "herbie hancock", "wes montgomery"],
            "classical": ["mozart", "beethoven", "bach", "chopin", "debussy"],
            "bollywood": ["a.r. rahman", "lata mangeshkar", "kishore kumar", "arijit singh"],
            "k-pop": ["bts", "blackpink", "twice", "red velvet", "exo"],
            "latin": ["bad bunny", "j balvin", "shakira", "enrique iglesias"]
        }
        
        # For now, return a mix of popular genres
        # In a real implementation, this would analyze the actual user data
        return ["rock", "pop", "indie", "alternative"]
    
    def _get_cultural_tags_for_country(self, country: str) -> List[str]:
        """Get cultural tags based on country"""
        cultural_mapping = {
            "IN": ["urn:tag:genre:music:bollywood", "urn:tag:genre:music:indian"],
            "US": ["urn:tag:genre:music:pop", "urn:tag:genre:music:hip_hop"],
            "UK": ["urn:tag:genre:music:pop", "urn:tag:genre:music:rock"],
            "CA": ["urn:tag:genre:music:pop", "urn:tag:genre:music:indie"],
            "AU": ["urn:tag:genre:music:pop", "urn:tag:genre:music:indie"],
            "DE": ["urn:tag:genre:music:electronic", "urn:tag:genre:music:rock"],
            "FR": ["urn:tag:genre:music:pop", "urn:tag:genre:music:electronic"],
            "JP": ["urn:tag:genre:music:j_pop", "urn:tag:genre:music:electronic"],
            "KR": ["urn:tag:genre:music:k_pop", "urn:tag:genre:music:pop"],
            "BR": ["urn:tag:genre:music:brazilian", "urn:tag:genre:music:pop"]
        }
        
        return cultural_mapping.get(country, ["urn:tag:genre:music:mainstream"]) 

    def _filter_recent_artists(self, recommendations: List[Dict]) -> List[Dict]:
        """Filter out recently recommended artists to prevent repetition"""
        filtered_recommendations = []
        target_count = 20  # Ensure we get at least 20 recommendations
        
        for rec in recommendations:
            artist_name = rec.get('name', '').lower().strip()
            if artist_name and artist_name not in self.recent_artists:
                filtered_recommendations.append(rec)
                # Add to recent artists (will be cleaned up later)
                self.recent_artists.add(artist_name)
                
                # If we have enough recommendations, stop filtering
                if len(filtered_recommendations) >= target_count:
                    break
        
        # If we don't have enough filtered recommendations, add some from the original list
        if len(filtered_recommendations) < target_count:
            remaining_needed = target_count - len(filtered_recommendations)
            for rec in recommendations:
                if rec not in filtered_recommendations:
                    filtered_recommendations.append(rec)
                    remaining_needed -= 1
                    if remaining_needed <= 0:
                        break
            
            # If still not enough, clear cache and try again
            if len(filtered_recommendations) < target_count:
                print(f"[VARIETY] Still need {target_count - len(filtered_recommendations)} more recommendations, clearing cache")
                self.recent_artists.clear()
                # Add more from original list
                for rec in recommendations:
                    if rec not in filtered_recommendations:
                        filtered_recommendations.append(rec)
                        if len(filtered_recommendations) >= target_count:
                            break
        
        # Clean up old entries if we have too many
        if len(self.recent_artists) > self.max_recent_artists:
            # Convert to list, remove oldest entries
            recent_list = list(self.recent_artists)
            self.recent_artists = set(recent_list[-self.max_recent_artists:])
        
        print(f"[VARIETY] Filtered out {len(recommendations) - len(filtered_recommendations)} recently recommended artists, kept {len(filtered_recommendations)}")
        return filtered_recommendations
    
    def _add_variety_to_recommendations(self, recommendations: List[Dict], variety_seed: int) -> List[Dict]:
        """Add variety to recommendations by shuffling and diversifying"""
        import random
        random.seed(variety_seed)
        
        # Filter out recently recommended artists
        filtered_recs = self._filter_recent_artists(recommendations)
        
        if not filtered_recs:
            # If all were filtered, use original but mark as repeated
            filtered_recs = recommendations
            print(f"[VARIETY] All artists were recently recommended, using original list")
        
        # Shuffle for variety
        random.shuffle(filtered_recs)
        
        return filtered_recs

    def clear_recent_artists_cache(self):
        """Clear the cache of recently recommended artists"""
        self.recent_artists.clear()
        print(f"[VARIETY] Cleared recent artists cache")
    
    def get_variety_stats(self) -> Dict:
        """Get statistics about variety and recent artists"""
        return {
            "recent_artists_count": len(self.recent_artists),
            "max_recent_artists": self.max_recent_artists,
            "cache_utilization": len(self.recent_artists) / self.max_recent_artists if self.max_recent_artists > 0 else 0
        }