from flask import Blueprint, request, jsonify
from services.spotify import SpotifyService
from services.qloo import QlooService
from services.gemini import GeminiService
from services.database import DatabaseService
from utils.helpers import (
    validate_input_data, sanitize_string, rank_recommendations_fast,
    apply_cultural_intelligence_fast, get_fallback_recommendations
)
import time
import hashlib
import json
from typing import Dict, List
import json
from typing import Dict, List

recommendation_routes = Blueprint('recommendations', __name__)
spotify_service = SpotifyService()
qloo_service = QlooService()
gemini_service = GeminiService()
db_service = DatabaseService()

# In-memory progress tracking
progress_tracker = {}

@recommendation_routes.route('/musicrecommendation', methods=['POST'])
@recommendation_routes.route('/musicrecommandation', methods=['POST'])
def music_recommendation():
    """Optimized music recommendation engine using Qloo + Gemini with enhanced user signals"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not validate_input_data(data, ["spotify_token"]):
            return jsonify({"error": "Missing required fields"}), 400
        
        spotify_token = sanitize_string(data["spotify_token"])
        user_context = sanitize_string(data.get("user_context", ""))
        limit = min(int(data.get("limit", 15)), 50)  # Cap at 50
        
        # Step 1: Get comprehensive user data from Spotify
        user_data = spotify_service.get_user_data_fast(spotify_token)
        if not user_data:
            return jsonify({"error": "Failed to get user data"}), 400
        
        user_id = user_data["profile"]["user_id"]
        user_country = user_data["profile"].get("country", "US")
        
        print(f"[USER DATA] User: {user_id}, Country: {user_country}")
        print(f"[USER DATA] Top artists: {[artist.get('name', '') for artist in user_data.get('artists', [])[:3]]}")
        
        # Step 2: Create user session for tracking
        session_id = db_service.create_user_session(user_id, spotify_token, user_country, user_context)
        
        # Step 3: No caching - always generate fresh recommendations
        print(f"[NO CACHE] Generating fresh recommendations for user {user_id}")
        
        # Step 4: Analyze context with Gemini
        context_analysis = gemini_service.analyze_context_fast(user_context)
        print(f"[CONTEXT] Analysis: {context_analysis}")
        
        # Step 5: Extract user's listening signals (artist and track IDs)
        user_artist_ids = [artist.get("id", "") for artist in user_data.get("artists", [])[:8]]
        user_track_ids = [track.get("id", "") for track in user_data.get("tracks", [])[:8]]
        
        print(f"[SIGNALS] User artist IDs: {user_artist_ids[:3]}...")
        print(f"[SIGNALS] User track IDs: {user_track_ids[:3]}...")
        
        # Step 6: Generate AI-driven context-aware tags
        context_tags = gemini_service.generate_context_aware_tags(user_context, user_country, user_artists)
        print(f"[AI TAGS] Context-aware tags: {context_tags}")

        # Step 6: Generate AI-driven context-aware tags
        context_tags = gemini_service.generate_context_aware_tags(user_context, user_country, user_artists)
        print(f"[AI TAGS] Context-aware tags: {context_tags}")

        # Generate cultural context
        cultural_context = gemini_service.generate_cultural_context(user_country, user_artists=user_artists)
        cultural_context = gemini_service.generate_cultural_context(user_country, user_artists=user_artists)
        print(f"[CULTURAL CONTEXT] Generated: {cultural_context}")

        # Create tags from cultural context

        # Create tags from cultural context
        cultural_tags = cultural_context.get("cultural_elements", []) + cultural_context.get("popular_genres", [])

        # Combine AI-generated context tags with cultural tags
        all_tags = context_tags + cultural_tags
        all_tags = list(dict.fromkeys(all_tags))  # Remove duplicates

        print(f"[TAGS] AI context tags: {context_tags}")

        print(f"[TAGS] AI context tags: {context_tags}")
        print(f"[TAGS] Cultural tags: {cultural_tags}")
        print(f"[TAGS] Combined tags: {all_tags}")
        
        # Send tags to Qloo until 5 are accepted
        tag_ids = []
        max_attempts = 10  # Prevent infinite loops
        attempt = 0
        
        while len(tag_ids) < 3 and attempt < max_attempts:  # Reduced minimum requirement
        while len(tag_ids) < 3 and attempt < max_attempts:  # Reduced minimum requirement
            attempt += 1
            print(f"[QLOO ATTEMPT {attempt}] Trying to get 5 accepted tags...")
            
            # Try current tag set
            current_tag_ids = qloo_service.get_tag_ids_fast(all_tags)
            tag_ids.extend(current_tag_ids)
            
            # Remove duplicates
            tag_ids = list(dict.fromkeys(tag_ids))
            
            print(f"[QLOO ATTEMPT {attempt}] Got {len(tag_ids)} accepted tags so far")
            
            # If we have 3 or more tags, we're done (no limit)
            if len(tag_ids) >= 3:
            # If we have 3 or more tags, we're done (no limit)
            if len(tag_ids) >= 3:
                print(f"[SUCCESS] Got {len(tag_ids)} accepted tags after {attempt} attempts")
                break
            
            # If we need more tags, add fallback tags
            if attempt < max_attempts - 1:
                print(f"[NEED MORE TAGS] Only got {len(tag_ids)} tags, adding fallback tags...")
                
                # Add fallback tags based on context
                fallback_tags = []
                if len(tag_ids) < 3:
                    fallback_tags = ['pop', 'mainstream', 'contemporary', 'cultural', 'diverse']
                elif len(tag_ids) < 4:
                    fallback_tags = ['energetic', 'upbeat', 'romantic', 'drama']
                else:
                    fallback_tags = ['electronic', 'dance', 'indie', 'alternative']
                
                all_tags.extend(fallback_tags)
                all_tags = list(dict.fromkeys(all_tags))  # Remove duplicates
                print(f"[FALLBACK] Added tags: {fallback_tags}")
        
        print(f"[FINAL RESULT] Using {len(tag_ids)} accepted tags: {tag_ids}")
        
        # Step 7: Get music recommendations using user signals
        recommendations = []
        
        if tag_ids and (user_artist_ids or user_track_ids):
            # Use enhanced method with user signals
            recommendations = qloo_service.get_music_recommendations_with_user_signals(
                tag_ids=tag_ids,
                user_artist_ids=user_artist_ids,
                user_track_ids=user_track_ids,
                user_country=user_country,
                limit=limit
            )
            print(f"[RECOMMENDATIONS] Got {len(recommendations)} recommendations with user signals")
        
        # Step 8: Fallback if no recommendations with signals
        if not recommendations and tag_ids:
            recommendations = qloo_service.get_recommendations_fast(tag_ids, limit)
            print(f"[FALLBACK] Got {len(recommendations)} recommendations without signals")
        
        # Step 9: Final fallback with hardcoded recommendations
        if not recommendations:
            print("[FINAL FALLBACK] Using hardcoded recommendations")
            recommendations = qloo_service.get_hardcoded_fallback_artists(
                cultural_context={"country": user_country},
                limit=limit
            )
        
        # Step 10: Apply cultural intelligence and ranking
        if recommendations:
            recommendations = apply_cultural_intelligence_fast(recommendations, user_country)
            
            user_preferences = {
                "artists": [artist["name"] for artist in user_data["artists"]],
                "tracks": [track["name"] for track in user_data["tracks"]]
            }
            
            recommendations = rank_recommendations_fast(recommendations, user_preferences)
            print(f"[RANKING] Final recommendations: {len(recommendations)}")
        
        # Step 11: Track new artists
        if recommendations:
            artist_data = [
                {
                    "name": rec.get("name", ""), 
                    "genre": rec.get("properties", {}).get("genres", [""])[0] if rec.get("properties", {}).get("genres") else "",
                    "popularity": rec.get("popularity", 0.0)
                } 
                for rec in recommendations if rec.get("name")
            ]
            db_service.track_new_artists(user_id, artist_data)
        
        # Step 12: Update user taste analytics
        if recommendations:
            for rec in recommendations:
                genres = rec.get("properties", {}).get("genres", [])
                if genres:
                    db_service.update_user_taste_analytics(user_id, genres[0], 1, 0, 0.0)
        
        # Step 13: Update mood preferences
        if context_analysis.get("primary_mood"):
            db_service.update_mood_preferences(user_id, context_analysis["primary_mood"], 1.0)
        
        # Step 14: Create playlist if requested
        playlist = None
        if data.get("create_playlist", False) and recommendations:
            playlist_name = f"SoniqueDNA - {context_analysis.get('activity_type', 'Music').title()}"
            playlist_description = f"AI-generated playlist for {context_analysis.get('primary_mood', 'music')} mood"
            
            playlist = spotify_service.create_playlist(spotify_token, user_id, playlist_name, playlist_description)
        
        response_time = time.time() - start_time
        
        # Step 15: Store in history
        db_service.store_recommendation_history(
            user_id=user_id,
            session_id=session_id,
            recommendation_type="music",
            user_context=user_context,
            generated_tags=all_tags,
            qloo_artists=recommendations,
            playlist_data={"recommendations": recommendations[:limit]},
            response_time=response_time
        )
        
        # Step 16: Prepare response data
        new_artists = db_service.get_new_artists(user_id, 5)
        
        # Calculate cultural tags count for showcase
        cultural_keywords = [
            "latin", "k-pop", "afrobeats", "jazz", "blues", "folk", "world", "bollywood", "hindi", "indian", 
            "cultural", "romantic", "drama", "adventure", "mystery", "comedy", "asian", "western", "european",
            "african", "middle_eastern", "south_asian", "desi", "pop", "mainstream", "contemporary", "traditional",
            "emotional", "upbeat", "energetic", "calm", "relaxation", "party", "workout", "study", "social"
        ]
        
        cultural_tags_found = [tag for tag in all_tags if any(cultural_word in tag.lower() for cultural_word in cultural_keywords)]
        cultural_tags_count = len(cultural_tags_found)
        
        # If no cultural tags found but we have tags, count it as at least 1
        if cultural_tags_count == 0 and all_tags:
            cultural_tags_count = 1
            print(f"[MUSIC REC] No cultural tags found in all_tags: {all_tags}, but tags exist")
        
        # Create qloo power showcase for music recommendations
        qloo_power_showcase = {
            "enhanced_system": True,
            "cultural_intelligence": bool(cultural_context),
            "location_awareness": False,  # Music recommendations don't use location
            "multi_strategy_recommendations": True,
            "cross_domain_analysis": False,  # This is music-specific
            "total_recommendations": len(recommendations),
            "cultural_tags_count": cultural_tags_count,
            "location_based_count": 0  # Music recommendations don't use location
        }
        
        response_data = {
            "playlist": playlist,
            "recommendations": recommendations[:limit],
            "new_artists": new_artists,
            "qloo_power_showcase": qloo_power_showcase,
            "from_cache": False,  # Always false since we removed caching
            "analysis": {
                "context_analysis": context_analysis,
                "tags_used": all_tags,
                "accepted_tags_count": len(tag_ids),
                "user_signals_count": len(user_artist_ids) + len(user_track_ids),
                "user_country": user_country,
                "response_time": round(response_time, 2),
                "cache_hit": False,
                "recommendation_method": "user_signals" if user_artist_ids or user_track_ids else "tag_based"
            }
        }
        
        # Step 17: No caching - skip cache storage
        
        print(f"[SUCCESS] Music recommendations completed in {round(response_time, 2)}s")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Music recommendation error: {e}")
        import traceback
        traceback.print_exc()
        
        # Enhanced fallback with better error handling
        try:
            fallback_recommendations = qloo_service.get_hardcoded_fallback_artists(
                cultural_context={"country": "US"},
                limit=limit
            )
        except:
            fallback_recommendations = get_fallback_recommendations("party")
        
        return jsonify({
            "playlist": None,
            "recommendations": fallback_recommendations,
            "new_artists": [],
            "analysis": {
                "context_analysis": {"primary_mood": "neutral", "activity_type": "general"},
                "tags_used": ["pop", "mainstream"],
                "fallback": True,
                "error": str(e),
                "response_time": round(time.time() - start_time, 2)
            }
        })

@recommendation_routes.route('/crossdomain-recommendations', methods=['POST'])
def crossdomain_recommendations():
    """Optimized multi-domain recommendations"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not validate_input_data(data, ["spotify_token"]):
            return jsonify({"error": "Missing required fields"}), 400
        
        spotify_token = sanitize_string(data["spotify_token"])
        limit = min(int(data.get("limit", 10)), 20)  # Cap at 20
        
        # Step 1: Get user data once with fallback
        user_data = spotify_service.get_user_data_fast(spotify_token)
        if not user_data:
            print("Profile fetch error: Failed to get user data from Spotify")
            # Return fallback recommendations instead of error
            return jsonify({
                "recommendations": {
                    "music artist": [],
                    "movie": [],
                    "TV show": [],
                    "podcast": [],
                    "book": []
                },
                "message": "Using fallback recommendations due to Spotify API issues",
                "fallback": True
            }), 200
        
        user_country = user_data["profile"].get("country", "US")
        user_id = user_data["profile"]["user_id"]
        
        print(f"[COUNTRY DEBUG] Cross-domain route - User Country: {user_country}")
        print(f"[COUNTRY DEBUG] User Profile: {user_data['profile']}")
        
        # Step 2: Create user session for tracking
        session_id = db_service.create_user_session(user_id, spotify_token, user_country, "cross-domain recommendations")
        
        # Step 2.5: Add cache busting for variety
        cache_bust = data.get("cache_bust", False)  # Allow frontend to request fresh data
        force_refresh = data.get("force_refresh", False)  # Force complete refresh
        
        # Create varied cache key to prevent repetitive results
        import time
        cache_variation = int(time.time() * 1000) % 1000  # Add time-based variation
        cache_key = hashlib.md5(f"{user_id}_crossdomain_{cache_variation}_{user_country}".encode()).hexdigest()
        
        # Only check cache if not forcing refresh
        if not force_refresh and not cache_bust:
            cached_result = db_service.get_cached_recommendation(cache_key)
            if cached_result:
                print(f"[CACHE HIT] Returning cached cross-domain result for user {user_id}")
                return jsonify(cached_result)
        
        # Step 3: Prepare top artists with images (with fallback)
        top_artists_with_images = []
        
        # Get artists with images directly from Spotify service
        artists_with_images = spotify_service.get_top_artists_with_images(spotify_token, limit=6, time_range="medium_term")
        
        if not artists_with_images:
            print("[CROSSDOMAIN] No artists data available, using fallback")
            # Use fallback artists for cultural context
            top_artists_with_images = [
                {"id": "fallback_1", "name": "The Weeknd", "image": None, "genres": ["pop", "r&b"], "popularity": 0.9, "followers": 0},
                {"id": "fallback_2", "name": "Ed Sheeran", "image": None, "genres": ["pop", "folk"], "popularity": 0.9, "followers": 0},
                {"id": "fallback_3", "name": "Taylor Swift", "image": None, "genres": ["pop", "country"], "popularity": 0.9, "followers": 0}
            ]
        else:
            # Use the artists with images data directly
            top_artists_with_images = artists_with_images[:6]
        
        # Step 3: Generate unified tags with variety
        import random
        import time
        
        # Create varied contexts to get different recommendations
        context_variations = [
            "cross-domain recommendations",
            "discover new entertainment",
            "explore diverse content",
            "find similar vibes",
            "cultural exploration",
            "entertainment discovery",
            "taste-based recommendations",
            "multi-media exploration"
        ]
        
        # Use timestamp-based selection for variety
        context_index = int(time.time() * 1000) % len(context_variations)
        context = context_variations[context_index]
        
        # Add user-specific variation based on their top artists
        if top_artists_with_images:
            top_artist = top_artists_with_images[0]["name"] if top_artists_with_images else ""
            if top_artist:
                context = f"{context} inspired by {top_artist}"
        
        # Step 3: Generate Qloo-optimized tags with cultural intelligence
        user_artists = [artist.get("name", "") for artist in top_artists_with_images[:5]]  # Get top 5 artist names
        if not user_artists:
            user_artists = ["The Weeknd", "Ed Sheeran", "Taylor Swift"]  # Fallback artists
        
        try:
            tags = gemini_service.generate_optimized_tags(context, user_country, user_artists)
            tag_ids = qloo_service.get_tag_ids_fast(tags)
        except Exception as e:
            print(f"Tag generation error: {e}")
            # Use fallback tags
            tags = ["mainstream", "contemporary", "cultural", "emotional"]  # Fallback tags
            tag_ids = qloo_service.get_fallback_tag_ids("music")
        
        # Step 4: Process all domains in parallel with correct mapping
        domains = ["artist", "movie", "tv_show", "podcast", "book"]  # Use correct Qloo domain names
        domain_mapping = {
            "artist": "music artist",      # Map to frontend expected name
            "movie": "movie",             # Same
            "tv_show": "TV show",         # Map to frontend expected name
            "podcast": "podcast",         # Same
            "book": "book"                # Same
        }
        recommendations_by_domain = {}
        for domain in domains:
            try:
                domain_recommendations = qloo_service.get_cross_domain_recommendations(tag_ids, domain, limit)
                frontend_domain = domain_mapping.get(domain, domain)
                recommendations_by_domain[frontend_domain] = domain_recommendations[:limit]
            except Exception as e:
                print(f"Domain {domain} error: {e}")
                frontend_domain = domain_mapping.get(domain, domain)
                recommendations_by_domain[frontend_domain] = []
        
        response_time = time.time() - start_time
        
        # Store cross-domain recommendation in history
        all_recommendations = []
        for domain, recs in recommendations_by_domain.items():
            all_recommendations.extend(recs)
        
        db_service.store_recommendation_history(
            user_id=user_id,
            session_id=session_id,
            recommendation_type="crossdomain",
            user_context="cross-domain recommendations",
            generated_tags=tags,
            qloo_artists=all_recommendations,
            playlist_data={"recommendations_by_domain": recommendations_by_domain},
            response_time=response_time
        )
        
        # Calculate cultural tags count for showcase
        cultural_keywords = [
            "latin", "k-pop", "afrobeats", "jazz", "blues", "folk", "world", "bollywood", "hindi", "indian", 
            "cultural", "romantic", "drama", "adventure", "mystery", "comedy", "asian", "western", "european",
            "african", "middle_eastern", "south_asian", "desi", "pop", "mainstream", "contemporary", "traditional",
            "emotional", "upbeat", "energetic", "calm", "relaxation", "party", "workout", "study", "social"
        ]
        
        cultural_tags_found = [tag for tag in tags if any(cultural_word in tag.lower() for cultural_word in cultural_keywords)]
        cultural_tags_count = len(cultural_tags_found)
        
        # If no cultural tags found but we have tags, count it as at least 1
        if cultural_tags_count == 0 and tags:
            cultural_tags_count = 1
            print(f"[CROSSDOMAIN] No cultural tags found in tags: {tags}, but tags exist")
        
        # Calculate total recommendations across all domains
        total_recommendations = sum(len(items) for items in recommendations_by_domain.values() if items)
        
        # Create qloo power showcase for cross-domain recommendations
        qloo_power_showcase = {
            "enhanced_system": True,
            "cultural_intelligence": True,
            "location_awareness": False,  # Cross-domain doesn't use location
            "multi_strategy_recommendations": True,
            "cross_domain_analysis": True,
            "total_recommendations": total_recommendations,
            "cultural_tags_count": cultural_tags_count,
            "location_based_count": 0  # Cross-domain doesn't use location
        }
        
        return jsonify({
            "top_artists": [artist["name"] for artist in top_artists_with_images],
            "top_artists_with_images": top_artists_with_images,
            "recommendations_by_domain": recommendations_by_domain,
            "total_domains": len([d for d in domains if recommendations_by_domain.get(d)]),
            "qloo_power_showcase": qloo_power_showcase,
            "analysis": {
                "tags_used": tags,
                "user_country": user_country,
                "response_time": round(response_time, 2)
            }
        })
        
    except Exception as e:
        print(f"Cross-domain recommendations error: {e}")
        return jsonify({"error": "Failed to get cross-domain recommendations"}), 500

@recommendation_routes.route('/crossdomain-progress/<user_id>', methods=['GET'])
def get_crossdomain_progress(user_id):
    """Real-time progress tracking"""
    try:
        progress = progress_tracker.get(user_id, {
            "percentage": 0,
            "status": "not_started",
            "current_artist": "",
            "current_domain": ""
        })
        
        return jsonify(progress)
        
    except Exception as e:
        print(f"Progress tracking error: {e}")
        return jsonify({"error": "Failed to get progress"}), 500

@recommendation_routes.route('/artist-priority-recommendations', methods=['POST'])
def artist_priority_recommendations():
    """Fast artist-based recommendations using Qloo artist search"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not validate_input_data(data, ["spotify_token", "artist_name"]):
            return jsonify({"error": "Missing required fields"}), 400
        
        spotify_token = sanitize_string(data["spotify_token"])
        artist_name = sanitize_string(data["artist_name"])
        context = sanitize_string(data.get("context", ""))
        limit = min(int(data.get("limit", 15)), 50)  # Cap at 50
        
        # Step 1: Get user data to get country for cultural context
        user_data = spotify_service.get_user_data_fast(spotify_token)
        if not user_data:
            return jsonify({"error": "Failed to get user data"}), 400
        
        user_country = user_data["profile"].get("country", "US")
        user_id = user_data["profile"]["user_id"]
        
        print(f"[ARTIST SEARCH] Searching for artist: {artist_name}")
        
        # Step 2: Search for artist in Qloo database first
        qloo_artist = qloo_service.search_entity(artist_name, "artist")
        
        if qloo_artist:
            print(f"[QLOO FOUND] Found artist in Qloo: {qloo_artist.get('name', 'Unknown')} (ID: {qloo_artist.get('id', 'Unknown')})")
            
            # Step 3: Get recommendations based on this specific artist
            artist_id = qloo_artist.get("id")
            if artist_id:
                # Use the artist's own tags and signals for recommendations
                recommendations = qloo_service.get_artist_recommendations_by_tags(
                    [],  # No specific tags, use artist signals
                    [artist_id],  # Use the found artist ID as signal
                    limit=limit
                )
                
                print(f"[RECOMMENDATIONS] Got {len(recommendations)} recommendations based on artist ID")
                
                # Step 4: Apply cultural intelligence and ranking
                recommendations = apply_cultural_intelligence_fast(recommendations, user_country)
                
                # Step 5: Analyze artist context
                artist_analysis = gemini_service.analyze_artist_context(artist_name, context)
                
                response_time = time.time() - start_time
                
                return jsonify({
                    "recommendations": recommendations,
                    "artist_analysis": artist_analysis,
                    "qloo_artist": qloo_artist,
                    "search_method": "qloo_artist_search",
                    "response_time": round(response_time, 2)
                })
        
        # Fallback: If artist not found in Qloo, use tag-based approach
        print(f"[QLOO NOT FOUND] Artist '{artist_name}' not found in Qloo, using tag-based approach")
        
        # Step 2b: Generate Qloo-optimized tags with cultural intelligence
        tags = gemini_service.generate_optimized_tags(f"{artist_name} {context}", user_country, [artist_name])
        tag_ids = qloo_service.get_tag_ids_fast(tags)
        
        # Step 3b: Get recommendations with tag-based approach
        recommendations = qloo_service.get_recommendations_fast(tag_ids, limit)
        
        # Step 4b: Apply cultural intelligence and ranking
        recommendations = apply_cultural_intelligence_fast(recommendations, user_country)
        
        # Step 5b: Analyze artist context
        artist_analysis = gemini_service.analyze_artist_context(artist_name, context)
        
        response_time = time.time() - start_time
        
        return jsonify({
            "recommendations": recommendations,
            "artist_analysis": artist_analysis,
            "qloo_artist": None,
            "search_method": "tag_based_fallback",
            "response_time": round(response_time, 2)
        })
        
    except Exception as e:
        print(f"Artist recommendations error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to get artist recommendations"}), 500

@recommendation_routes.route('/history/<user_id>', methods=['GET'])
def get_user_history(user_id):
    """Get user's recommendation history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = db_service.get_user_history(user_id, limit)
        return jsonify({"history": history})
    except Exception as e:
        print(f"History fetch error: {e}")
        return jsonify({"error": "Failed to get history"}), 500

@recommendation_routes.route('/history/<user_id>/<int:history_id>', methods=['POST'])
def replay_recommendation(user_id, history_id):
    """Replay a specific recommendation from history"""
    try:
        history_item = db_service.get_history_item(history_id)
        if not history_item:
            return jsonify({"error": "History item not found"}), 404
        
        # Re-run recommendation with same context
        data = request.get_json()
        spotify_token = data.get("spotify_token")
        
        if not spotify_token:
            return jsonify({"error": "Missing spotify_token"}), 400
        
        # Use the stored context to generate new recommendations
        user_context = history_item.get("user_context", "")
        
        # Create a new request with the historical context
        replay_data = {
            "spotify_token": spotify_token,
            "user_context": user_context,
            "limit": 15
        }
        
        # Create a new request with the historical context
        request._json = replay_data
        return music_recommendation()
        
    except Exception as e:
        print(f"Replay recommendation error: {e}")
        return jsonify({"error": "Failed to replay recommendation"}), 500

@recommendation_routes.route('/new-artists/<user_id>', methods=['GET'])
def get_new_artists(user_id):
    """Get recently discovered new artists for user"""
    try:
        days = request.args.get('days', 7, type=int)
        print(f"Fetching new artists for user {user_id} in last {days} days")
        new_artists = db_service.get_new_artists(user_id, days)
        print(f"Found {len(new_artists)} new artists: {[artist['artist_name'] for artist in new_artists]}")
        return jsonify({"new_artists": new_artists})
    except Exception as e:
        print(f"New artists fetch error: {e}")
        return jsonify({"error": "Failed to get new artists"}), 500

@recommendation_routes.route('/taste-analytics/<user_id>', methods=['GET'])
def get_user_taste_analytics(user_id):
    """Get user taste analytics for graph visualization"""
    try:
        analytics = db_service.get_user_taste_analytics(user_id)
        return jsonify(analytics)
    except Exception as e:
        print(f"Taste analytics fetch error: {e}")
        return jsonify({"error": "Failed to get taste analytics"}), 500

@recommendation_routes.route('/artists/track', methods=['POST'])
def track_artists():
    """Track artists for new detection"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        artists = data.get('artists', [])
        
        if not user_id or not artists:
            return jsonify({"error": "Missing user_id or artists"}), 400
        
        new_artists = db_service.track_new_artists(user_id, artists)
        return jsonify({"new_artists": new_artists})
    except Exception as e:
        print(f"Artist tracking error: {e}")
        return jsonify({"error": "Failed to track artists"}), 500

@recommendation_routes.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Clear recommendation cache"""
    try:
        data = request.get_json()
        user_id = data.get("user_id") if data else None
        
        db_service.clear_user_cache(user_id)
        
        if user_id:
            print(f"Cleared cache for user: {user_id}")
        else:
            print("Cleared all cache")
        
        return jsonify({"status": "success", "message": "Cache cleared"})
        
    except Exception as e:
        print(f"Cache clearing error: {e}")
        return jsonify({"error": "Failed to clear cache"}), 500

@recommendation_routes.route('/analytics/clear/<user_id>', methods=['POST'])
def clear_analytics(user_id):
    """Clear analytics data for a user"""
    try:
        db_service.clear_user_analytics(user_id)
        return jsonify({"status": "success", "message": "Analytics cleared"})
    except Exception as e:
        print(f"Analytics clearing error: {e}")
        return jsonify({"error": "Failed to clear analytics"}), 500

@recommendation_routes.route('/artist-details', methods=['POST'])
def get_artist_details():
    """Get detailed artist information from Spotify"""
    try:
        data = request.get_json()
        
        if not data or not data.get("spotify_token") or not data.get("artist_name"):
            return jsonify({"error": "Missing spotify_token or artist_name"}), 400
        
        spotify_token = data["spotify_token"]
        artist_name = data["artist_name"]
        
        print(f"Searching for artist: {artist_name}")
        # First search for the artist to get their ID
        artist_search = spotify_service.search_artist(spotify_token, artist_name)
        
        if not artist_search:
            print(f"Artist '{artist_name}' not found in Spotify search")
            return jsonify({"error": f"Artist '{artist_name}' not found"}), 404
        
        print(f"Found artist in search: {artist_search.get('name', 'Unknown')} (ID: {artist_search.get('id', 'Unknown')})")
        # Get detailed artist information
        artist_details = spotify_service.get_artist_details(spotify_token, artist_search["id"])
        
        if not artist_details:
            return jsonify({"error": "Failed to get artist details"}), 500
        
        return jsonify({"artist": artist_details})
        
    except Exception as e:
        print(f"Artist details error: {e}")
        return jsonify({"error": "Failed to get artist details"}), 500

@recommendation_routes.route('/analytics/populate-sample/<user_id>', methods=['POST'])
def populate_sample_analytics(user_id):
    """Populate sample analytics data for a user"""
    try:
        db_service.populate_sample_analytics(user_id)
        return jsonify({"status": "success", "message": "Sample analytics populated"})
    except Exception as e:
        print(f"Sample analytics population error: {e}")
        return jsonify({"error": "Failed to populate sample analytics"}), 500 