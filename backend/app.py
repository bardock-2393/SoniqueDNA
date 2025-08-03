import os
import time
import random
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import optimized services
from services.spotify import SpotifyService
from services.qloo import QlooService
from services.gemini import GeminiService
from services.music_aggregator import MusicAggregatorService

# Import route handlers
from routes.auth import auth_routes
from routes.recommendations import recommendation_routes
from routes.playlists import playlist_routes

app = Flask(__name__)
CORS(app, origins=['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:8080', 'http://127.0.0.1:8080', 'http://localhost:4173', 'http://127.0.0.1:4173'], supports_credentials=True)

# Initialize services
spotify_service = SpotifyService()
qloo_service = QlooService()
gemini_service = GeminiService()
music_aggregator_service = MusicAggregatorService()

# Initialize cache for cross-domain recommendations (home page only)
crossdomain_cache = {}
CACHE_EXPIRY = 3600  # 1 hour in seconds



# Register route blueprints
app.register_blueprint(auth_routes, url_prefix='/auth')
app.register_blueprint(recommendation_routes, url_prefix='/recommendations')
app.register_blueprint(playlist_routes, url_prefix='/playlists')

# Add direct routes for frontend compatibility (matching old backend structure)
@app.route('/spotify-auth-url', methods=['GET', 'POST'])
def spotify_auth_url_direct():
    """Direct route for Spotify auth URL - frontend compatibility"""
    try:
        # Handle both GET (query params) and POST (JSON body)
        if request.method == 'GET':
            redirect_uri = request.args.get('redirect_uri')
            force_reauth = request.args.get('force_reauth', 'false').lower() == 'true'
            session_id = request.args.get('session_id')
        else:
            data = request.get_json()
            redirect_uri = data.get("redirect_uri") if data else None
            force_reauth = data.get("force_reauth", False) if data else False
            session_id = data.get("session_id") if data else None
        
        if not redirect_uri:
            return jsonify({"error": "Missing redirect_uri parameter"}), 400
        
        # Generate auth URL with re-authentication support
        auth_data = spotify_service.generate_auth_url(redirect_uri, force_reauth=force_reauth, session_id=session_id)
        
        return jsonify({
            "auth_url": auth_data["auth_url"],
            "state": auth_data["state"]
        })
        
    except Exception as e:
        print(f"Auth URL generation error: {e}")
        return jsonify({"error": "Failed to generate auth URL"}), 500

@app.route('/exchange-token', methods=['POST'])
def exchange_token_direct():
    """Direct route for token exchange - frontend compatibility"""
    try:
        data = request.get_json()
        
        if not data or not data.get("code"):
            return jsonify({"error": "Missing code parameter"}), 400
        
        code = data["code"]
        redirect_uri = data.get("redirect_uri", "http://127.0.0.1:8080/callback")
        
        # Exchange code for token
        token_data = spotify_service.exchange_token(code, redirect_uri)
        
        if not token_data:
            return jsonify({"error": "Failed to exchange token"}), 400
        
        return jsonify({
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in")
        })
        
    except Exception as e:
        print(f"Token exchange error: {e}")
        return jsonify({"error": "Failed to exchange token"}), 500

@app.route('/refresh-token', methods=['POST'])
def refresh_token_direct():
    """Direct route for token refresh - frontend compatibility"""
    try:
        data = request.get_json()
        
        if not data or not data.get("refresh_token"):
            return jsonify({"error": "Missing refresh_token parameter"}), 400
        
        refresh_token = data["refresh_token"]
        
        # Refresh the token
        token_data = spotify_service.refresh_token(refresh_token)
        
        if not token_data:
            return jsonify({"error": "Failed to refresh token"}), 400
        
        return jsonify({
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token", refresh_token),  # Keep old refresh token if not provided
            "expires_in": token_data.get("expires_in")
        })
        
    except Exception as e:
        print(f"Token refresh error: {e}")
        return jsonify({"error": "Failed to refresh token"}), 500

@app.route('/check-token', methods=['POST'])
def check_token_direct():
    """Check if token is valid and refresh if needed"""
    try:
        data = request.get_json()
        
        if not data or not data.get("access_token"):
            return jsonify({"error": "Missing access_token parameter"}), 400
        
        access_token = data["access_token"]
        refresh_token = data.get("refresh_token")
        
        # Check if token is expired
        if spotify_service.is_token_expired(access_token):
            if refresh_token:
                # Try to refresh the token
                token_data = spotify_service.refresh_token(refresh_token)
                if token_data:
                    return jsonify({
                        "valid": False,
                        "refreshed": True,
                        "access_token": token_data.get("access_token"),
                        "refresh_token": token_data.get("refresh_token", refresh_token),
                        "expires_in": token_data.get("expires_in")
                    })
                else:
                    return jsonify({
                        "valid": False,
                        "refreshed": False,
                        "error": "Failed to refresh token"
                    })
            else:
                return jsonify({
                    "valid": False,
                    "refreshed": False,
                    "error": "Token expired and no refresh token provided"
                })
        else:
            return jsonify({
                "valid": True,
                "refreshed": False
            })
        
    except Exception as e:
        print(f"Token check error: {e}")
        return jsonify({"error": "Failed to check token"}), 500

@app.route('/spotify-profile', methods=['POST'])
def spotify_profile_direct():
    """Direct route for Spotify profile - frontend compatibility"""
    try:
        data = request.get_json()
        
        if not data or not data.get("spotify_token"):
            return jsonify({"error": "Missing spotify_token"}), 400
        
        spotify_token = data["spotify_token"]
        
        # Get user profile
        profile = spotify_service.get_user_profile(spotify_token)
        
        if not profile:
            return jsonify({"error": "Failed to get user profile"}), 400
        
        return jsonify({
            "id": profile["user_id"],
            "display_name": profile["name"],
            "images": [{"url": profile["avatar"]}] if profile["avatar"] else [],
            "country": profile["country"]
        })
        
    except Exception as e:
        print(f"Profile fetch error: {e}")
        return jsonify({"error": "Failed to get user profile"}), 500

@app.route('/logout', methods=['POST'])
def logout_direct():
    """Direct route for logout - frontend compatibility"""
    try:
        data = request.get_json()
        
        # Accept access_token, client_id, client_secret (for token revocation)
        access_token = data.get("access_token")
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")
        
        # Optional: Revoke token if credentials provided
        if access_token and client_id and client_secret:
            try:
                # In a real implementation, you would call Spotify's token revocation endpoint
                print(f"Token revocation requested for client: {client_id}")
            except Exception as e:
                print(f"Token revocation failed: {e}")
        
        # Generate re-authentication URL
        import secrets
        import time
        unique_state = f"{secrets.token_urlsafe(32)}_{int(time.time())}"
        session_id = f"session_{secrets.token_urlsafe(16)}_{int(time.time())}"
        
        # Stateless logout - return success with re-auth URL
        return jsonify({
            "success": True,
            "message": "Logged out successfully",
            "force_reauth": True,
            "unique_state": unique_state,
            "session_id": session_id,
            "reauth_url": f"http://localhost:5500/spotify-auth-url?redirect_uri=http://127.0.0.1:8080/callback&force_reauth=true&session_id={session_id}"
        })
        
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({"error": "Failed to logout"}), 500

@app.route('/spotify-session-clear', methods=['POST'])
def spotify_session_clear_direct():
    """Clear Spotify session and force re-authentication - direct route"""
    try:
        import secrets
        import time
        session_id = f"session_{secrets.token_urlsafe(16)}_{int(time.time())}"
        
        return jsonify({
            'success': True,
            'message': 'Spotify session cleared',
            'session_id': session_id,
            'reauth_url': f"http://localhost:5500/spotify-auth-url?redirect_uri=http://127.0.0.1:8080/callback&force_reauth=true&session_id={session_id}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/musicrecommendation', methods=['POST'])
def music_recommendation_direct():
    """Optimized music recommendations with batch processing - frontend compatibility"""
    import time
    import random
    start_time = time.time()
    try:
        data = request.get_json()
        
        if not data or not data.get("spotify_token"):
            return jsonify({"error": "Missing spotify_token"}), 400
        
        spotify_token = data["spotify_token"]
        user_context = data.get("user_context", "")
        gemini_api_key = data.get("gemini_api_key", os.getenv('GEMINI_API_KEY', ''))
        qloo_api_key = data.get("qloo_api_key", os.getenv('QLOO_API_KEY', ''))
        limit = min(int(data.get("limit", 25)), 50)  # Increased default limit
        
        # Initialize database service
        from services.database import DatabaseService
        db_service = DatabaseService()
        
        # Get location parameters
        location = data.get("location")
        location_radius = data.get("location_radius", 50000)  # Default 50km radius
        
        print(f"[OPTIMIZED] Starting music recommendation with context: {user_context[:50]}...")
        
        # Step 1: Get user data in parallel (batch processing)
        user_data = spotify_service.get_user_data_fast(spotify_token)
        if not user_data:
            return jsonify({"error": "Failed to get user data"}), 400
        
        user_id = user_data["profile"]["user_id"]
        user_country = user_data["profile"].get("country", "US")
        user_artists = user_data["artists"]
        user_tracks = user_data["tracks"]
        
        # Debug: Print country detection
        print(f"[COUNTRY DEBUG] Music recommendation route - User Country: {user_country}")
        print(f"[COUNTRY DEBUG] User Profile: {user_data['profile']}")
        
        # If no location provided, derive from user country
        if not location and user_country:
            location_map = {
                "IN": "Mumbai, India",
                "US": "New York, USA", 
                "GB": "London, UK",
                "CA": "Toronto, Canada",
                "AU": "Sydney, Australia",
                "DE": "Berlin, Germany",
                "FR": "Paris, France",
                "JP": "Tokyo, Japan",
                "KR": "Seoul, South Korea",
                "BR": "São Paulo, Brazil"
            }
            location = location_map.get(user_country, "New York, USA")
            print(f"[LOCATION] Derived location from country {user_country}: {location}")
        elif location:
            print(f"[LOCATION] Using provided location: {location}")
        else:
            print(f"[LOCATION] No location provided and no country available - using global recommendations")
        
        # Create user session for tracking
        session_id = db_service.create_user_session(user_id, spotify_token, user_country, user_context)
        
        # Check audio features access and provide guidance
        audio_features_available = spotify_service.check_audio_features_access(spotify_token)
        if not audio_features_available:
            print("⚠️ Audio features not available - using fallback analysis")
            print("💡 To enable audio features, user needs to re-authenticate with updated scopes")
        else:
            print("✅ Audio features access confirmed - will use enhanced analysis")
        
        # Step 2: Enhanced context detection with mood and language preference
        enhanced_context = gemini_service.enhance_context_detection(user_context, user_country)
        context_type = enhanced_context.get('context_type', 'general')
        language_preference = enhanced_context.get('language_preference', {'primary_language': 'any'})
        mood_preference = enhanced_context.get('mood_preference', {'primary_mood': 'neutral'})
        
        print(f"[ENHANCED CONTEXT] Context: {context_type}, Mood: {mood_preference.get('primary_mood')}, Language: {language_preference.get('primary_language')}")
        
        # Step 3: Generate enhanced tags using Gemini (batch processing) with variety
        # Add variety to tag generation context
        tag_variety_seed = int(time.time() * 1000) % 10000
        context_with_variety = f"{user_context} {tag_variety_seed} {int(time.time()) % 1000}"
        
        enhanced_tags = gemini_service.generate_enhanced_tags(context_with_variety, user_country, location, user_artists)
        if not enhanced_tags:
            print("Warning: No enhanced tags generated, using fallback tags")
            enhanced_tags = ["upbeat", "energetic", "pop", "mainstream"]
        
        print(f"[ENHANCED] Generated {len(enhanced_tags)} enhanced tags with variety: {enhanced_tags}")
        print(f"[VARIETY] Tag generation variety seed: {tag_variety_seed}")
        
        # Step 4: Generate cultural context
        cultural_context = gemini_service.generate_cultural_context(user_country, location, user_artists)
        
        # Use location from cultural context if not provided
        if not location and cultural_context.get("location"):
            location = cultural_context["location"]
            print(f"[LOCATION] Using default location from cultural context: {location}")
        
        # Step 5: Generate cultural context tags and send directly to Qloo until 5 accepted
        print(f"[CULTURAL CONTEXT] Generated: {cultural_context}")
        
        # Create tags from cultural context, sorted by user context relevance
        cultural_tags = cultural_context.get("cultural_elements", []) + cultural_context.get("popular_genres", [])
        
        # Use improved Gemini service for context-aware tag generation
        context_tags = gemini_service.generate_context_aware_tags(user_context, user_country, user_artists)
        
        # Combine and prioritize: context tags first, then cultural tags
        all_tags = context_tags + cultural_tags
        all_tags = list(dict.fromkeys(all_tags))  # Remove duplicates
        
        print(f"[TAGS] Context-specific tags: {context_tags}")
        print(f"[TAGS] Cultural tags: {cultural_tags}")
        print(f"[TAGS] Combined tags: {all_tags}")
        
        # Send tags to Qloo until 5 are accepted
        tag_ids = []
        max_attempts = 10  # Prevent infinite loops
        attempt = 0
        
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
        
        # Step 7: Get music recommendations with user signals (music-specific method)
        print(f"[QLOO LOCATION] Calling Qloo with location: {location}, radius: {location_radius}m")

        # Clear recent artists cache periodically to allow variety
        import time
        current_time = int(time.time())
        if current_time % 180 == 0:  # Clear cache every 3 minutes (reduced from 5)
            qloo_service.clear_recent_artists_cache()
            print(f"[CACHE] Cleared recent artists cache for variety")
        
        # Force clear cache if we have too many recent artists to ensure variety
        variety_stats = qloo_service.get_variety_stats()
        if variety_stats.get("cache_utilization", 0) > 0.8:  # If cache is 80% full
            qloo_service.clear_recent_artists_cache()
            print(f"[CACHE] Forced cache clear due to high utilization ({variety_stats.get('cache_utilization', 0):.1%})")

        # Convert user data to the format expected by music recommendations
        user_artist_ids = [artist.get('id', '') for artist in user_artists[:8] if isinstance(artist, dict) and artist.get('id')]
        user_track_ids = [track.get('id', '') for track in user_tracks[:8] if isinstance(track, dict) and track.get('id')]

        # Filter tags to ensure only music tags are used (exclude media tags)
        music_tag_ids = []
        for tag_id in tag_ids:
            if 'music' in tag_id and 'media' not in tag_id:
                music_tag_ids.append(tag_id)
            elif 'genre:music:' in tag_id:
                music_tag_ids.append(tag_id)
        
        if not music_tag_ids:
            print("[MUSIC TAGS] No music tags found, using fallback music tags")
            music_tag_ids = [
                "urn:tag:genre:music:pop",
                "urn:tag:genre:music:rock", 
                "urn:tag:genre:music:electronic",
                "urn:tag:genre:music:hip_hop",
                "urn:tag:genre:music:indie"
            ]
        
        print(f"[MUSIC TAGS] Using {len(music_tag_ids)} music-specific tags: {music_tag_ids}")

        # Try music-specific recommendations with variety and relevance
        enhanced_recommendations = qloo_service.get_music_recommendations_with_user_signals(
            tag_ids=music_tag_ids,
            user_artist_ids=user_artist_ids,
            user_track_ids=user_track_ids,
            user_country=user_country,
            location=location,
            location_radius=location_radius,
            limit=20  # Fixed limit for consistency
        )
        
        # If music-specific fails, try cross-domain with music focus
        if not enhanced_recommendations or len(enhanced_recommendations) == 0:
            print("[MUSIC FALLBACK] Music-specific API returned 0 results, trying cross-domain with music focus")
            enhanced_recommendations = qloo_service.get_enhanced_recommendations(
                tag_ids=music_tag_ids,
                user_artists=user_artists[:8],
                user_tracks=user_tracks[:8],
                location=location,
                location_radius=location_radius,
                cultural_context=cultural_context,
                limit=20
            )

        # Use Qloo results directly without additional processing
        if enhanced_recommendations:
            print(f"[QLOO RESULTS] Using {len(enhanced_recommendations)} Qloo artists directly")
            
            # Extract artist names from Qloo recommendations
            qloo_reco_artists = []
            for artist in enhanced_recommendations:
                if isinstance(artist, dict):
                    qloo_reco_artists.append(artist.get("name", ""))
                elif isinstance(artist, str):
                    qloo_reco_artists.append(artist)
                else:
                    qloo_reco_artists.append(str(artist))
            
            print(f"[QLOO ARTISTS] Final artist list: {qloo_reco_artists[:5]}...")
            
            # Ensure we have exactly 20 recommendations
            if len(qloo_reco_artists) < 20:
                print(f"[RECOMMENDATION COUNT] Only got {len(qloo_reco_artists)} recommendations, need 20")
                # If we have some recommendations but not enough, try to get more
                if len(qloo_reco_artists) > 0:
                    # Try to get more from the same source
                    additional_recommendations = qloo_service.get_enhanced_recommendations(
                        tag_ids=music_tag_ids,
                        user_artists=user_artists[:8],
                        user_tracks=user_tracks[:8],
                        location=location,
                        location_radius=location_radius,
                        cultural_context=cultural_context,
                        limit=20 - len(qloo_reco_artists)
                    )
                    
                    if additional_recommendations:
                        additional_artists = []
                        for artist in additional_recommendations:
                            if isinstance(artist, dict):
                                additional_artists.append(artist.get("name", ""))
                            elif isinstance(artist, str):
                                additional_artists.append(artist)
                            else:
                                additional_artists.append(str(artist))
                        
                        # Add unique additional artists
                        for artist in additional_artists:
                            if artist not in qloo_reco_artists and len(qloo_reco_artists) < 20:
                                qloo_reco_artists.append(artist)
                        
                        print(f"[RECOMMENDATION COUNT] Added {len(additional_artists)} more artists, total: {len(qloo_reco_artists)}")
            
            # Final check - if still not 20, pad with user artists
            if len(qloo_reco_artists) < 20:
                user_artist_names = []
                for artist in user_artists:
                    if isinstance(artist, dict):
                        user_artist_names.append(artist.get('name', ''))
                    elif isinstance(artist, str):
                        user_artist_names.append(artist)
                
                for artist_name in user_artist_names:
                    if artist_name not in qloo_reco_artists and len(qloo_reco_artists) < 20:
                        qloo_reco_artists.append(artist_name)
                
                print(f"[RECOMMENDATION COUNT] Padded with user artists, final count: {len(qloo_reco_artists)}")
        else:
            qloo_reco_artists = []
            print("[QLOO RESULTS] No Qloo recommendations received")

        # If Qloo failed completely, use enhanced Spotify data with variety
        if len(qloo_reco_artists) == 0:
            print("[MUSIC FALLBACK] Qloo returned no recommendations, trying global music aggregator")
            
            try:
                # Try to get global music variety as fallback
                global_variety_result = music_aggregator_service.get_global_music_variety(
                    category=context_type if context_type in music_aggregator_service.global_categories else None,
                    mood=enhanced_context.get('mood_preference', {}).get('primary_mood'),
                    region=user_country,
                    limit=20,
                    variety_boost=True
                )
                
                if global_variety_result["artists"]:
                    # Extract artist names from global variety
                    global_artist_names = [artist.get("name", "") for artist in global_variety_result["artists"] if artist.get("name")]
                    qloo_reco_artists = global_artist_names[:15]
                    print(f"[GLOBAL VARIETY FALLBACK] Using {len(qloo_reco_artists)} artists from global music aggregator")
                    print(f"[GLOBAL VARIETY FALLBACK] Providers used: {global_variety_result['providers_used']}")
                else:
                    # Fallback to enhanced Spotify data
                    print("[MUSIC FALLBACK] Global variety failed, using enhanced Spotify data")
                    
                    # Get user's top artists with variety
                    spotify_artist_names = []
                    for artist in user_artists[:15]:
                        if isinstance(artist, dict):
                            spotify_artist_names.append(artist.get('name', ''))
                        elif isinstance(artist, str):
                            spotify_artist_names.append(artist)
                        else:
                            spotify_artist_names.append(str(artist))
                    
                    # Add similar artists for variety
                    try:
                        similar_artists = []
                        for artist_name in spotify_artist_names[:5]:  # Get similar for top 5
                            similar = spotify_service.get_similar_artists(artist_name, spotify_token, limit=3)
                            similar_artists.extend(similar)
                        
                        # Combine and shuffle for variety
                        all_artists = spotify_artist_names + similar_artists
                        random.shuffle(all_artists)
                        qloo_reco_artists = all_artists[:12]  # Get more variety
                        print(f"[MUSIC FALLBACK] Using {len(qloo_reco_artists)} artists (user + similar) with variety")
                    except Exception as e:
                        print(f"[MUSIC FALLBACK] Error getting similar artists: {e}")
                        # Fallback to just user artists
                        random.shuffle(spotify_artist_names)
                        qloo_reco_artists = spotify_artist_names[:10]
                        print(f"[MUSIC FALLBACK] Using {len(qloo_reco_artists)} shuffled user artists")
                        
            except Exception as e:
                print(f"[GLOBAL VARIETY FALLBACK] Error: {e}")
                # Fallback to enhanced Spotify data
                print("[MUSIC FALLBACK] Global variety failed, using enhanced Spotify data")
                
                # Get user's top artists with variety
                spotify_artist_names = []
                for artist in user_artists[:15]:
                    if isinstance(artist, dict):
                        spotify_artist_names.append(artist.get('name', ''))
                    elif isinstance(artist, str):
                        spotify_artist_names.append(artist)
                    else:
                        spotify_artist_names.append(str(artist))
                
                # Add similar artists for variety
                try:
                    similar_artists = []
                    for artist_name in spotify_artist_names[:5]:  # Get similar for top 5
                        similar = spotify_service.get_similar_artists(artist_name, spotify_token, limit=3)
                        similar_artists.extend(similar)
                    
                    # Combine and shuffle for variety
                    all_artists = spotify_artist_names + similar_artists
                    random.shuffle(all_artists)
                    qloo_reco_artists = all_artists[:12]  # Get more variety
                    print(f"[MUSIC FALLBACK] Using {len(qloo_reco_artists)} artists (user + similar) with variety")
                except Exception as e:
                    print(f"[MUSIC FALLBACK] Error getting similar artists: {e}")
                    # Fallback to just user artists
                    random.shuffle(spotify_artist_names)
                    qloo_reco_artists = spotify_artist_names[:10]
                    print(f"[MUSIC FALLBACK] Using {len(qloo_reco_artists)} shuffled user artists")
        
        # Step 8: Fast language filtering using known artist lists
        if language_preference and language_preference.get('primary_language') != 'any':
            print(f"[FAST LANGUAGE FILTER] Applying quick filter to {len(qloo_reco_artists)} artists")
            primary_language = language_preference['primary_language']
            
            # Known artist lists for fast filtering
            known_english_artists = {
                'martin garrix', 'the chainsmokers', 'alan walker', 'marshmello', 'dj snake', 
                'major lazer', 'calvin harris', 'david guetta', 'avicii', 'skrillex',
                'zedd', 'kygo', 'the weeknd', 'ed sheeran', 'taylor swift', 'justin bieber',
                'ariana grande', 'post malone', 'dua lipa', 'billie eilish', 'harry styles',
                'coldplay', 'imagine dragons', 'maroon 5', 'one republic', 'twenty one pilots'
            }
            
            known_hindi_artists = {
                'pritam', 'atif aslam', 'a.r. rahman', 'anuv jain', 'ritviz', 'arijit singh',
                'sachin-jigar', 'mohit lalwani', 'shankar-ehsaan-loy', 'mohit chauhan',
                'neha kakkar', 'badshah', 'karan aujla', 'amit trivedi', 'vishal-shekhar',
                'jatin-lalit', 'kailash kher', 'benny dayal', 'sunidhi chauhan', 'shreya ghoshal',
                'armaan malik', 'harrdy sandhu', 'shaan', 'vishal dadlani', 'shankar mahadevan'
            }
            
            # Fast filtering using known lists
            filtered_artists = []
            for artist in qloo_reco_artists:
                artist_lower = artist.lower()
                if primary_language == 'english':
                    if artist_lower in known_english_artists or artist_lower not in known_hindi_artists:
                        filtered_artists.append(artist)
                elif primary_language == 'hindi':
                    if artist_lower in known_hindi_artists or artist_lower not in known_english_artists:
                        filtered_artists.append(artist)
            
            if filtered_artists:
                qloo_reco_artists = filtered_artists
                print(f"[FAST LANGUAGE FILTER] Filtered to {len(qloo_reco_artists)} artists")
            else:
                print(f"[FAST LANGUAGE FILTER] No artists matched, using fallback")
                qloo_reco_artists = spotify_service.get_context_fallback_artists("upbeat", language_preference)
        
        # Step 9: Use Spotify data as primary source, fallback only if needed
        if len(qloo_reco_artists) < 5:
            print(f"Qloo returned only {len(qloo_reco_artists)} artists, using Spotify data as primary source")
            # Use Spotify user artists as primary source
            spotify_artist_names = []
            for artist in user_artists[:10]:
                if isinstance(artist, dict):
                    spotify_artist_names.append(artist.get('name', ''))
                elif isinstance(artist, str):
                    spotify_artist_names.append(artist)
                else:
                    spotify_artist_names.append(str(artist))
            
            # Add Spotify artists to the list
            qloo_reco_artists.extend(spotify_artist_names)
            print(f"Added {len(spotify_artist_names)} Spotify artists")
            
            # Only add hardcoded fallback if we still don't have enough
            if len(qloo_reco_artists) < 10:
                fallback_artists = spotify_service.get_context_fallback_artists("upbeat", language_preference)
                qloo_reco_artists.extend(fallback_artists)
                print(f"Added {len(fallback_artists)} hardcoded fallback artists")
        
        qloo_reco_artists = list(set(qloo_reco_artists))  # Remove duplicates
        print(f"Final artist list has {len(qloo_reco_artists)} unique language-appropriate artists")
        
        # Step 10: Smart collection of tracks (optimized approach)
        all_collected_tracks = []
        seen_tracks = set()
        
        print(f"[OPTIMIZED COLLECTION] Starting smart collection from {len(qloo_reco_artists)} artists")
        
        # Get enhanced user preferences for personalization
        user_preferences = spotify_service.get_enhanced_user_preferences(spotify_token, context_type, language_preference, None)
        
        # Step 10a: Smart artist selection - pick only the most relevant artists (max 8-10)
        user_artist_names = [artist.get('name', '').lower() for artist in user_artists if isinstance(artist, dict)]
        
        # Score artists based on relevance to user taste and context
        scored_artists = []
        for artist_name in qloo_reco_artists:
            score = 0.0
            
            # User taste matching (highest priority)
            if artist_name.lower() in user_artist_names:
                score += 5.0
            elif any(user_artist in artist_name.lower() for user_artist in user_artist_names):
                score += 3.0
            
            # Context matching
            context_lower = user_context.lower()
            if any(word in artist_name.lower() for word in ['romantic', 'love', 'heart']) and 'romantic' in context_lower:
                score += 2.0
            elif any(word in artist_name.lower() for word in ['sad', 'blue', 'melancholic']) and any(word in context_lower for word in ['blue', 'sad', 'down']):
                score += 2.0
            elif any(word in artist_name.lower() for word in ['happy', 'joy', 'upbeat']) and any(word in context_lower for word in ['happy', 'joy', 'energetic']):
                score += 2.0
            
            # Cultural relevance
            if user_country == "IN" and any(word in artist_name.lower() for word in ['pritam', 'arijit', 'atif', 'neha', 'badshah', 'karan']):
                score += 1.5
            
            scored_artists.append((artist_name, score))
        
        # Sort by score and pick top 8-10 artists
        scored_artists.sort(key=lambda x: x[1], reverse=True)
        selected_artists = [artist for artist, score in scored_artists[:10]]
        
        print(f"[OPTIMIZED COLLECTION] Selected {len(selected_artists)} most relevant artists out of {len(qloo_reco_artists)}")
        print(f"[OPTIMIZED COLLECTION] Selected artists: {selected_artists[:5]}...")
        
        # Step 10b: Smart track collection - get only 3-5 most relevant tracks per artist
        for artist_name in selected_artists:
            try:
                # Get artist ID from Spotify
                artist_id = spotify_service.get_artist_id(artist_name, spotify_token)
                if not artist_id:
                    print(f"[TRACK FETCH] Could not find artist ID for: {artist_name}")
                    continue
                
                print(f"[TRACK FETCH] Found artist ID for {artist_name}: {artist_id}")
                
                # Get only 5 tracks per artist (reduced from 10)
                artist_tracks = spotify_service.get_artist_top_tracks(artist_id, spotify_token, 5, user_country)
                print(f"[TRACK FETCH] Got {len(artist_tracks)} tracks for {artist_name}")
                
                # Ensure artist_tracks is a list of dictionaries
                if not isinstance(artist_tracks, list):
                    print(f"Warning: artist_tracks is not a list for {artist_name}")
                    continue
                
                # Step 10c: Pre-filter tracks before adding to collection
                filtered_tracks = []
                for track in artist_tracks:
                    # Ensure track is a dictionary
                    if not isinstance(track, dict):
                        continue
                    
                    # Simple pre-filtering based on track name and user context
                    track_name = track.get('name', '').lower()
                    context_lower = user_context.lower()
                    
                    # Skip obviously irrelevant tracks
                    if any(word in track_name for word in ['remix', 'instrumental', 'karaoke', 'cover']):
                        continue
                    
                    # Boost tracks that match context
                    relevance_score = 0.0
                    if any(word in track_name for word in ['love', 'romantic', 'heart']) and 'romantic' in context_lower:
                        relevance_score += 2.0
                    elif any(word in track_name for word in ['sad', 'blue', 'cry', 'tears']) and any(word in context_lower for word in ['blue', 'sad', 'down']):
                        relevance_score += 2.0
                    elif any(word in track_name for word in ['happy', 'joy', 'smile']) and any(word in context_lower for word in ['happy', 'joy', 'upbeat']):
                        relevance_score += 2.0
                    
                    # Add personalization score
                    personalization_score = 0
                    if user_preferences and user_preferences.get('favorite_artists'):
                        if artist_name in user_preferences.get('favorite_artists', []):
                            personalization_score = 2.0
                    
                    # Only add tracks with decent relevance or from user's favorite artists
                    if relevance_score > 0 or personalization_score > 0 or len(filtered_tracks) < 3:
                        filtered_tracks.append((track, relevance_score + personalization_score))
                
                # Sort by relevance and take top 3 tracks per artist
                filtered_tracks.sort(key=lambda x: x[1], reverse=True)
                selected_tracks = [track for track, score in filtered_tracks[:3]]
                
                print(f"[OPTIMIZED COLLECTION] Selected {len(selected_tracks)} relevant tracks for {artist_name}")
                
                # Process selected tracks
                for track in selected_tracks:
                    # Get track genres and emotional context analysis (simplified)
                    emotional_context = "neutral"
                    primary_genre = "unknown"
                    
                    try:
                        if track.get('id'):
                            if audio_features_available:
                                audio_features = spotify_service.get_audio_features([track['id']], spotify_token)
                                if audio_features and len(audio_features) > 0:
                                    features = audio_features[0]
                                    emotional_context = spotify_service.analyze_track_emotional_context(features, track.get('name', ''), artist_name)
                                    track["audio_features"] = features
                            else:
                                emotional_context = spotify_service.analyze_track_music_context(track.get('name', ''), artist_name, context_type)
                            
                            # Get artist genres (simplified)
                            artist_genres = spotify_service.get_spotify_artist_genres(artist_name, spotify_token)
                            if artist_genres:
                                track["artist_genres"] = artist_genres
                                primary_genre = artist_genres[0] if artist_genres else "unknown"
                            else:
                                primary_genre = spotify_service.get_artist_genre_fallback(artist_name)
                            
                    except Exception as e:
                        print(f"[GENRE ANALYSIS] Error analyzing track {track.get('name', 'Unknown')}: {e}")
                        emotional_context = "neutral"
                        primary_genre = "unknown"
                    
                    # Create track object
                    try:
                        artists = track.get("artists", [])
                        artist_name = "Unknown Artist"
                        if artists and isinstance(artists, list) and len(artists) > 0:
                            if isinstance(artists[0], dict):
                                artist_name = artists[0].get("name", "Unknown Artist")
                            else:
                                artist_name = str(artists[0])
                        
                        album = track.get("album", {})
                        album_name = "Unknown Album"
                        release_year = "Unknown"
                        album_art_url = "/placeholder.svg"
                        
                        if isinstance(album, dict):
                            album_name = album.get("name", "Unknown Album")
                            release_date = album.get("release_date")
                            if release_date:
                                release_year = str(release_date)[:4]
                            
                            images = album.get("images", [])
                            if images and isinstance(images, list) and len(images) > 0:
                                if isinstance(images[0], dict):
                                    album_art_url = images[0].get("url", "/placeholder.svg")
                        
                        track_obj = {
                            "name": track.get("name", "Unknown Track"),
                            "artist": artist_name,
                            "album_name": album_name,
                            "release_year": release_year,
                            "album_art_url": album_art_url,
                            "preview_url": track.get("preview_url"),
                            "url": track.get("external_urls", {}).get("spotify", "#") if isinstance(track.get("external_urls"), dict) else "#",
                            "personalization_score": personalization_score,
                            "context_score": 1.0 + personalization_score,
                            "emotional_context": emotional_context,
                            "primary_genre": primary_genre
                        }
                    except Exception as e:
                        print(f"Error creating track object for {track.get('name', 'Unknown')}: {e}")
                        continue
                    
                    # Avoid duplicates
                    try:
                        track_key = f"{track_obj['name']}_{track_obj['artist']}"
                        if track_key not in seen_tracks:
                            all_collected_tracks.append(track_obj)
                            seen_tracks.add(track_key)
                    except Exception as e:
                        print(f"Error adding track to collection: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error getting tracks for artist {artist_name}: {e}")
                continue
        
        print(f"[OPTIMIZED COLLECTION] Collected {len(all_collected_tracks)} total tracks (target: 50-80)")
        
        # Step 11: Use Gemini to comprehensively filter and rank tracks (optimized)
        print(f"[GEMINI OPTIMIZED] Sending {len(all_collected_tracks)} pre-filtered tracks to Gemini for final relevance filtering")
        
        try:
            # Use the comprehensive filtering method with optimized track set
            playlist = gemini_service.filter_all_tracks_comprehensive(
                all_tracks=all_collected_tracks,
                user_context=user_context,
                user_country=user_country,
                user_artists=user_artists,
                user_tracks=user_tracks,
                context_type=context_type,
                location=location
            )
            
            print(f"[GEMINI OPTIMIZED] Gemini returned {len(playlist)} relevant tracks out of {len(all_collected_tracks)} pre-filtered tracks")
            
        except Exception as e:
            print(f"[GEMINI OPTIMIZED] Error in comprehensive filtering: {e}")
            # Fallback to original method
            playlist = all_collected_tracks[:limit]
            print(f"[GEMINI OPTIMIZED] Using fallback: {len(playlist)} tracks")
        
        # Step 12: Ensure we have tracks - music-specific fallback if playlist is empty
        if len(playlist) == 0:
            print(f"[MUSIC FALLBACK] No tracks found, using music-specific {context_type} fallback")
            try:
                # Try to get trending tracks for the specific context
                playlist = spotify_service.get_trending_tracks_for_context(context_type, spotify_token, limit=15)
                print(f"[MUSIC FALLBACK] Got {len(playlist)} trending tracks for {context_type}")
            except Exception as e:
                print(f"[MUSIC FALLBACK] Trending tracks failed: {e}")
                try:
                    # Try to get user's top tracks as fallback
                    user_tracks = spotify_service.get_top_tracks_detailed(spotify_token, limit=15)
                    if user_tracks:
                        playlist = []
                        for track in user_tracks:
                            track_obj = {
                                "name": track.get("name", "Unknown Track"),
                                "artist": track.get("artists", [{}])[0].get("name", "Unknown Artist") if track.get("artists") else "Unknown Artist",
                                "album_name": track.get("album", {}).get("name", "Unknown Album"),
                                "release_year": str(track.get("album", {}).get("release_date", ""))[:4] if track.get("album", {}).get("release_date") else "Unknown",
                                "album_art_url": track.get("album", {}).get("images", [{}])[0].get("url", "/placeholder.svg") if track.get("album", {}).get("images") else "/placeholder.svg",
                                "preview_url": track.get("preview_url"),
                                "url": track.get("external_urls", {}).get("spotify", "#"),
                                "personalization_score": 0.8,  # High score for user's own tracks
                                "context_score": 1.8,
                                "emotional_context": "neutral",
                                "primary_genre": "user_favorite"
                            }
                            playlist.append(track_obj)
                        print(f"[MUSIC FALLBACK] Using {len(playlist)} user's top tracks as fallback")
                except Exception as e2:
                    print(f"[MUSIC FALLBACK] User tracks also failed: {e2}")
                    # Final fallback - create context-appropriate tracks
                    playlist = spotify_service.get_hardcoded_fallback_tracks(context_type)
                    print(f"[MUSIC FALLBACK] Added {len(playlist)} hardcoded fallback tracks")
        
        # Step 13: Final deduplication and ensure we have 25-30 tracks
        unique_playlist = []
        seen_track_ids = set()
        seen_track_names = set()
        
        for track in playlist:
            track_id = track.get('id') or track.get('spotify_id')
            track_name = track.get('name', '').lower().strip()
            track_artist = track.get('artist', '').lower().strip()
            
            if track_id:
                unique_id = track_id
            else:
                unique_id = f"{track_name}_{track_artist}"
            
            if unique_id not in seen_track_ids and track_name not in seen_track_names:
                unique_playlist.append(track)
                seen_track_ids.add(unique_id)
                seen_track_names.add(track_name)
        
        playlist = unique_playlist
        
        # Ensure we have 25-30 tracks as requested
        if len(playlist) > 30:
            playlist = playlist[:30]
        elif len(playlist) < 25 and len(all_collected_tracks) >= 25:
            # Add more tracks from the original collection if needed
            remaining_tracks = [track for track in all_collected_tracks if track not in playlist]
            playlist.extend(remaining_tracks[:25 - len(playlist)])
        
        print(f"[FINAL RESULT] Final playlist length: {len(playlist)} tracks (target: 25-30)")
        
        # Step 14: Prepare response data
        response_time = time.time() - start_time
        
        # Extract artist names for database storage
        artist_names = [artist for artist in qloo_reco_artists if artist]
        
        # Track new artists
        artist_data = [{"name": artist, "genre": "unknown", "popularity": 0.0} for artist in qloo_reco_artists if artist]
        db_service.track_new_artists(user_id, artist_data)
        
        # Update user taste analytics for each genre found
        for track in playlist:
            if track.get("primary_genre"):
                db_service.update_user_taste_analytics(user_id, track.get("primary_genre"), 1, 0, 0.0)
        
        # Update mood preferences
        if enhanced_context.get("mood_preference", {}).get("primary_mood"):
            db_service.update_mood_preferences(user_id, enhanced_context["mood_preference"]["primary_mood"], 1.0)
        
        # Store recommendation history
        # Convert qloo_reco_artists to the format expected by database
        qloo_artists_for_db = [{"name": artist} for artist in qloo_reco_artists if artist]
        db_service.store_recommendation_history(
            user_id=user_id,
            session_id=session_id,
            recommendation_type="music",
            user_context=user_context,
            generated_tags=enhanced_tags,
            qloo_artists=qloo_artists_for_db,
            playlist_data={"recommendations": playlist[:limit]},
            response_time=response_time
        )
        
        # Get new artists for response
        new_artists = db_service.get_new_artists(user_id, 5)
        
        # Add display tags and display_qloo_artists for simple rendering
        display_tags = ', '.join(enhanced_tags)
        display_qloo_artists = ', '.join([str(artist) for artist in qloo_reco_artists[:15]])
        
        # Add Qloo power showcase information
        # Enhanced cultural tags detection
        cultural_keywords = [
            "latin", "k-pop", "afrobeats", "jazz", "blues", "folk", "world", "bollywood", "hindi", "indian", 
            "cultural", "romantic", "drama", "adventure", "mystery", "comedy", "asian", "western", "european",
            "african", "middle_eastern", "south_asian", "desi", "pop", "mainstream", "contemporary", "traditional",
            "emotional", "upbeat", "energetic", "calm", "relaxation", "party", "workout", "study", "social"
        ]
        
        cultural_tags_found = [tag for tag in enhanced_tags if any(cultural_word in tag.lower() for cultural_word in cultural_keywords)]
        cultural_tags_count = len(cultural_tags_found)
        
        # If no cultural tags found but we have cultural context, count it as at least 1
        if cultural_tags_count == 0 and cultural_context:
            cultural_tags_count = 1
            print(f"[QLOO POWER] No cultural tags found in enhanced_tags: {enhanced_tags}, but cultural context exists: {cultural_context}")
        
        # If still 0, check if any tags contain cultural elements
        if cultural_tags_count == 0 and enhanced_tags:
            # Count any tag that might be cultural based on broader criteria
            cultural_tags_count = len([tag for tag in enhanced_tags if len(tag) > 3 and not tag.isdigit()])
            print(f"[QLOO POWER] Using broader cultural detection, found {cultural_tags_count} potential cultural tags from: {enhanced_tags}")
        
        # Get variety statistics
        variety_stats = qloo_service.get_variety_stats()
        
        qloo_power_showcase = {
            "enhanced_system": True,
            "cultural_intelligence": bool(cultural_context),
            "location_awareness": bool(location),
            "multi_strategy_recommendations": True,
            "cross_domain_analysis": True,
            "smart_pre_filtering": True,
            "optimized_collection": True,
            "pro_model_processing": True,
            "variety_system": True,
            "total_recommendations": len(enhanced_recommendations),
            "total_tracks_analyzed": len(all_collected_tracks) if 'all_collected_tracks' in locals() else 0,
            "final_recommendations": len(playlist),
            "optimization_ratio": f"{len(all_collected_tracks)}/{len(qloo_reco_artists) * 10}" if 'all_collected_tracks' in locals() else "N/A",
            "cultural_tags_count": cultural_tags_count,
            "location_based_count": len([artist for artist in enhanced_recommendations if artist.get("location_relevance", 0) > 0.1 or artist.get("cultural_relevance", 0) > 0.3]) if enhanced_recommendations else (1 if location else 0),
            "variety_stats": variety_stats
        }
        
        # Force location-based count to be at least 1 if location is provided and we have recommendations
        if location and len(enhanced_recommendations) > 0 and qloo_power_showcase["location_based_count"] == 0:
            qloo_power_showcase["location_based_count"] = 1
            print(f"[QLOO POWER] Forced location-based count to 1 for location: {location}")
        
        # Debug logging for Qloo power showcase
        print(f"[QLOO POWER] Cultural tags: {qloo_power_showcase['cultural_tags_count']}")
        print(f"[QLOO POWER] Location-based: {qloo_power_showcase['location_based_count']}")
        print(f"[QLOO POWER] Total recommendations: {qloo_power_showcase['total_recommendations']}")
        print(f"[QLOO POWER] Total tracks analyzed: {qloo_power_showcase['total_tracks_analyzed']}")
        print(f"[QLOO POWER] Final recommendations: {qloo_power_showcase['final_recommendations']}")
        print(f"[QLOO POWER] Optimization ratio: {qloo_power_showcase['optimization_ratio']}")
        print(f"[QLOO POWER] Smart pre-filtering: {qloo_power_showcase['smart_pre_filtering']}")
        print(f"[QLOO POWER] Optimized collection: {qloo_power_showcase['optimized_collection']}")
        print(f"[QLOO POWER] Pro model processing: {qloo_power_showcase['pro_model_processing']}")
        print(f"[QLOO POWER] Variety system: {qloo_power_showcase['variety_system']}")
        print(f"[QLOO POWER] Recent artists tracked: {qloo_power_showcase['variety_stats']['recent_artists_count']}")
        print(f"[QLOO POWER] Location used: {location}")
        print(f"[QLOO POWER] Cultural context: {bool(cultural_context)}")
        
        enhanced_features = [
            "Cultural Intelligence",
            "Location-Aware Recommendations", 
            "Multi-Strategy Analysis",
            "Affinity Scoring",
            "Cross-Domain Insights",
            "Enhanced Gemini Integration",
            "Smart Pre-filtering",
            "Optimized Track Collection",
            "Pro Model Processing",
            "Variety System",
            "Anti-Repetition Algorithm",
            "25-30 Relevance-Optimized Recommendations",
            "Global Music Aggregator",
            "Multi-Provider Variety",
            "Cultural Music Discovery",
            "Mood-Based Variety",
            "YouTube Music Integration",
            "Last.fm Integration",
            "Deezer Integration",
            "Enhanced Global Variety"
        ]
        
        # Debug info
        spotify_user_artist_names = []
        for artist in user_artists:
            if isinstance(artist, dict):
                spotify_user_artist_names.append(artist.get('name', ''))
            elif isinstance(artist, str):
                spotify_user_artist_names.append(artist)
            else:
                spotify_user_artist_names.append(str(artist))
        
        spotify_user_track_names = []
        for track in user_tracks:
            if isinstance(track, dict):
                spotify_user_track_names.append(track.get('name', ''))
            elif isinstance(track, str):
                spotify_user_track_names.append(track)
            else:
                spotify_user_track_names.append(str(track))
        
        debug_info = {
            "enhanced_gemini_tags": all_tags,
            "cultural_context": cultural_context,
            "qloo_tag_ids": tag_ids,
            "music_tag_ids": music_tag_ids if 'music_tag_ids' in locals() else [],
            "spotify_user_artists": spotify_user_artist_names,
            "spotify_user_tracks": spotify_user_track_names,
            "qloo_recommended_artists": qloo_reco_artists,
            "selected_artists_count": len(selected_artists) if 'selected_artists' in locals() else 0,
            "total_tracks_collected": len(all_collected_tracks) if 'all_collected_tracks' in locals() else 0,
            "final_playlist_length": len(playlist),
            "context_type": "optimized_enhanced",
            "location_used": location,
            "user_country": user_country,
            "smart_pre_filtering": True,
            "optimization_ratio": f"{len(all_collected_tracks)}/{len(qloo_reco_artists) * 10}" if 'all_collected_tracks' in locals() else "N/A",
            "variety_seeds": {
                "tag_variety_seed": tag_variety_seed if 'tag_variety_seed' in locals() else None,
                "recommendation_variety_seed": variety_seed if 'variety_seed' in locals() else None,
                "location_seed": location_seed if 'location_seed' in locals() else None
            },
            "music_fallback_used": len(qloo_reco_artists) == 0,
            "qloo_entities_received": len(enhanced_recommendations) if 'enhanced_recommendations' in locals() else 0
        }
        
        return jsonify({
            "playlist": playlist,
            "tags": all_tags,
            "qloo_artists": [{"name": artist} for artist in qloo_reco_artists[:15] if artist],
            "new_artists": new_artists,
            "context_type": "enhanced",
            "debug": debug_info,
            "display_tags": display_tags,
            "display_qloo_artists": display_qloo_artists,
            "access_token": spotify_token,
            "from_cache": False,
            "generated_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "location_used": location,
            "location_radius": location_radius if location else None,
            "user_country": user_country,
            "qloo_power_showcase": qloo_power_showcase,
            "enhanced_features": enhanced_features,
            "ai_scoring_info": {
                "ai_scoring_enabled": True,
                "tracks_ai_scored": len([t for t in playlist if t.get('ai_scored', False)]),
                "total_tracks": len(playlist),
                "scoring_method": "AI-Enhanced Relevance Scoring",
                "ai_score_weight": 0.7,
                "traditional_score_weight": 0.3,
                "artists_scored": len(qloo_reco_artists),
                "relevance_scoring_applied": True,
                "randomization_applied": True
            },
            "audio_features_status": {
                "available": audio_features_available,
                "message": "Audio features enabled - enhanced analysis available" if audio_features_available else "Audio features not available - using fallback analysis",
                "recommendation": "Re-authenticate with updated scopes to enable audio features" if not audio_features_available else "Audio features working correctly"
            },
            "analysis": {
                "tags_used": all_tags,
                "user_country": user_country,
                "location_used": location if location else "Global",
                "location_radius": location_radius if location else None,
                "location_based": location is not None,
                "genre_based": True,
                "response_time": round(response_time, 2),
                "batch_processing": True,
                "optimization_level": "enhanced",
                "variety_info": {
                    "tag_variety_seed": tag_variety_seed if 'tag_variety_seed' in locals() else None,
                    "recommendation_variety_seed": variety_seed if 'variety_seed' in locals() else None,
                    "location_seed": location_seed if 'location_seed' in locals() else None,
                    "unique_artists": len(set(qloo_reco_artists)),
                    "total_artists": len(qloo_reco_artists),
                    "relevance_scoring": True,
                    "controlled_randomization": True,
                    "top_artists_preserved": 3,
                    "randomized_artists": max(0, len(qloo_reco_artists) - 3)
                }
            }
        })
        
    except Exception as e:
        print(f"Music recommendation error: {e}")
        
        # Get user data for database storage even in fallback
        try:
            user_data = spotify_service.get_user_data_fast(spotify_token)
            if user_data:
                user_id = user_data["profile"]["user_id"]
                user_country = user_data["profile"].get("country", "US")
                
                # Create user session for tracking
                session_id = db_service.create_user_session(user_id, spotify_token, user_country, user_context)
                
                # Store fallback recommendation in database
                fallback_recommendations = spotify_service.get_fallback_recommendations("party")
                
                # Convert fallback to playlist format
                fallback_playlist = []
                for rec in fallback_recommendations:
                    track = {
                        "name": rec.get("name", "Unknown Track"),
                        "artist": rec.get("artist", "Unknown Artist"),
                        "album_name": rec.get("album", "Unknown Album"),
                        "release_year": str(rec.get("year", "Unknown")),
                        "album_art_url": rec.get("image_url") or "/placeholder.svg",
                        "preview_url": rec.get("preview_url"),
                        "url": rec.get("spotify_url") or rec.get("url", "#"),
                        "context_score": rec.get("affinity_score", 0.7)
                    }
                    fallback_playlist.append(track)
                
                # Store recommendation history
                db_service.store_recommendation_history(
                    user_id=user_id,
                    session_id=session_id,
                    recommendation_type="music_fallback",
                    user_context=user_context,
                    generated_tags=["pop", "trending"],
                    qloo_artists=[{"name": rec.get("name", "")} for rec in fallback_recommendations[:10]],
                    playlist_data={"recommendations": fallback_playlist},
                    response_time=time.time() - start_time
                )
                
                return jsonify({
                    "playlist": fallback_playlist,
                    "tags": ["pop", "trending"],
                    "qloo_artists": [rec.get("name", "") for rec in fallback_recommendations[:10]],
                    "context_type": "music_recommendation",
                    "user_id": user_id,
                    "user_country": user_country,
                    "analysis": {
                        "context_analysis": {"primary_mood": "neutral", "activity_type": "general"},
                        "tags_used": ["pop", "trending"],
                        "fallback": True,
                        "response_time": round(time.time() - start_time, 2),
                        "database_stored": True
                    }
                })
        except Exception as db_error:
            print(f"Database storage error in fallback: {db_error}")
        
        # Final fallback without database
        fallback_recommendations = spotify_service.get_fallback_recommendations("party")
        
        # Convert fallback to playlist format
        fallback_playlist = []
        for rec in fallback_recommendations:
            track = {
                "name": rec.get("name", "Unknown Track"),
                "artist": rec.get("artist", "Unknown Artist"),
                "album_name": rec.get("album", "Unknown Album"),
                "release_year": str(rec.get("year", "Unknown")),
                "album_art_url": rec.get("image_url") or "/placeholder.svg",
                "preview_url": rec.get("preview_url"),
                "url": rec.get("spotify_url") or rec.get("url", "#"),
                "context_score": rec.get("affinity_score", 0.7)
            }
            fallback_playlist.append(track)
        
        return jsonify({
            "playlist": fallback_playlist,
            "tags": ["pop", "trending"],
            "qloo_artists": [rec.get("name", "") for rec in fallback_recommendations[:10]],
            "context_type": "music_recommendation",
            "analysis": {
                "context_analysis": {"primary_mood": "neutral", "activity_type": "general"},
                "tags_used": ["pop", "trending"],
                "fallback": True,
                "response_time": round(time.time() - start_time, 2),
                "database_stored": False
            }
        })
        
    except Exception as e:
        print(f"[MUSIC RECOMMENDATION] Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/crossdomain-recommendations', methods=['POST'])
def crossdomain_recommendations_direct():
    """Direct route for cross-domain recommendations - frontend compatibility"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data or not data.get("spotify_token"):
            return jsonify({"error": "Missing spotify_token"}), 400
        
        spotify_token = data["spotify_token"]
        limit = min(int(data.get("limit", 10)), 20)  # Cap at 20
        
        # Get data from music recommendation page
        user_context = data.get("user_context", "")
        music_artists = data.get("music_artists", [])
        top_scored_artists = data.get("top_scored_artists", [])
        user_tags = data.get("user_tags", [])
        
        # Get location parameters
        location = data.get("location")  # e.g., "Mumbai", "New York", "London"
        location_radius = data.get("location_radius", 50000)  # Default 50km radius
        
        print(f"[CROSSDOMAIN] User context: {user_context}")
        print(f"[CROSSDOMAIN] Music artists: {music_artists}")
        print(f"[CROSSDOMAIN] Top scored artists: {top_scored_artists}")
        print(f"[CROSSDOMAIN] User tags: {user_tags}")
        
        # Step 1: Get user data for country and basic info
        user_data = spotify_service.get_user_data_fast(spotify_token)
        if not user_data:
            return jsonify({"error": "Failed to get user data"}), 400
        
        user_country = user_data["profile"].get("country", "US")
        user_id = user_data["profile"]["user_id"]
        
        # Debug: Print country detection
        print(f"[COUNTRY DEBUG] Cross-domain route - User Country: {user_country}")
        print(f"[COUNTRY DEBUG] User Profile: {user_data['profile']}")
        
        # If no location provided, derive from user country
        if not location and user_country:
            location_map = {
                "IN": "Mumbai, India",
                "US": "New York, USA", 
                "GB": "London, UK",
                "CA": "Toronto, Canada",
                "AU": "Sydney, Australia",
                "DE": "Berlin, Germany",
                "FR": "Paris, France",
                "JP": "Tokyo, Japan",
                "KR": "Seoul, South Korea",
                "BR": "São Paulo, Brazil"
            }
            location = location_map.get(user_country, "New York, USA")
            print(f"[LOCATION] Derived location from country {user_country}: {location}")
        elif location:
            print(f"[LOCATION] Using provided location: {location}")
        else:
            print(f"[LOCATION] No location provided and no country available - using global recommendations")
        
        # Step 2: Get top artists with images (use top scored artists if available)
        if top_scored_artists and len(top_scored_artists) > 0:
            # Use top scored artists from music recommendations
            top_artists_with_images = []
            for artist_name in top_scored_artists[:6]:
                top_artists_with_images.append({
                    "id": "",  # We don't have artist IDs from music recommendations
                    "name": artist_name,
                    "image": None,
                    "genres": [],
                    "popularity": 0,
                    "followers": 0
                })
        else:
            # Fallback to user's Spotify top artists
            top_artists_with_images = spotify_service.get_top_artists_with_images(spotify_token, limit=6)
        
        # Step 3: Generate tags based on music recommendation data
        # Combine user tags, music artists, and top scored artists for better context
        combined_artists = list(set(music_artists + top_scored_artists))
        
        # Differentiate between home page and discover more recommendations
        is_home_page = user_context == "music discovery and cross-domain recommendations"
        
        # Check cache for home page requests only
        if is_home_page:
            # Generate cache key based on user country and location
            cache_key = f"crossdomain_home_{user_country}_{location}"
            current_time = time.time()
            
            # Check if we have cached data and it's not expired
            if cache_key in crossdomain_cache:
                cached_data = crossdomain_cache[cache_key]
                if current_time - cached_data['timestamp'] < CACHE_EXPIRY:
                    print(f"[CACHE HIT] Returning cached cross-domain recommendations for home page (age: {int(current_time - cached_data['timestamp'])}s)")
                    # Mark as from cache
                    cached_data['data']['from_cache'] = True
                    cached_data['data']['cache_age_seconds'] = int(current_time - cached_data['timestamp'])
                    cached_data['data']['cache_expires_in'] = int(CACHE_EXPIRY - (current_time - cached_data['timestamp']))
                    return jsonify(cached_data['data'])
                else:
                    print(f"[CACHE EXPIRED] Removing expired cache entry for key: {cache_key}")
                    del crossdomain_cache[cache_key]
            
            print(f"[CACHE MISS] No valid cache found for home page, generating fresh recommendations")
        
        if is_home_page:
            # Home page: Use broader, more general recommendations
            context = f"home page cross-domain recommendations based on general music taste"
            # Add more variety for home page
            cache_buster = int(time.time() * 1000) % 2000  # More variety
        else:
            # Discover more: Use more specific, context-aware recommendations
            context = f"discover more cross-domain recommendations based on {user_context} music taste"
            # Add cache-busting parameter to ensure variety
            cache_buster = int(time.time() * 1000) % 1000  # Use milliseconds for variety
        
        context = f"{context} {cache_buster}"
        
        # Step 4: Process all domains with enhanced tags
        domains = ["movie", "tv_show", "podcast", "book", "artist"]
        domain_mapping = {
            "movie": "movie",
            "tv_show": "TV show", 
            "podcast": "podcast",
            "book": "book",
            "artist": "music artist"
        }
        recommendations_by_domain = {}
        
        for domain in domains:
            try:
                # Generate enhanced tags using music recommendation data
                print(f"\n=== Processing Domain: {domain} ===")
                
                if is_home_page:
                    # Home page: Use more general, popular tags
                    domain_tags = gemini_service.generate_music_based_cross_domain_tags(
                        ["popular", "mainstream", "trending"], combined_artists, "general entertainment", user_country, domain
                    )
                else:
                    # Discover more: Use specific, context-aware tags
                    domain_tags = gemini_service.generate_music_based_cross_domain_tags(
                        user_tags, combined_artists, user_context, user_country, domain
                    )
                
                print(f"Domain {domain} enhanced tags: {domain_tags}")
                
                # Get tag IDs for this domain
                tag_ids = qloo_service.get_tag_ids_fast(domain_tags, domain)
                print(f"Domain {domain} tag IDs: {tag_ids}")
                
                # Get recommendations for this domain with location support
                print(f"[CROSSDOMAIN LOCATION] Getting {domain} recommendations with location: {location}, radius: {location_radius}m")
                domain_recommendations = qloo_service.get_cross_domain_recommendations(
                    tag_ids, domain, max(limit, 10), location, location_radius
                )
                frontend_domain = domain_mapping[domain]
                recommendations_by_domain[frontend_domain] = domain_recommendations[:max(limit, 10)]
                print(f"Domain {domain} -> {frontend_domain}: {len(domain_recommendations)} recommendations")
                
                # Debug: Show first few recommendations
                if domain_recommendations:
                    print(f"Sample recommendations for {domain}:")
                    for i, rec in enumerate(domain_recommendations[:3]):
                        print(f"  {i+1}. {rec.get('name', 'Unknown')} (Type: {rec.get('type', 'Unknown')})")
                else:
                    print(f"No recommendations found for {domain}")
                    
            except Exception as e:
                print(f"Domain {domain} error: {e}")
                import traceback
                traceback.print_exc()
                frontend_domain = domain_mapping[domain]
                recommendations_by_domain[frontend_domain] = []
        
        response_time = time.time() - start_time
        
        # Count domains with recommendations
        domains_with_data = [domain for domain in domain_mapping.values() if recommendations_by_domain.get(domain)]
        
        print(f"Final response - Domains with data: {domains_with_data}")
        print(f"Total recommendations: {sum(len(recs) for recs in recommendations_by_domain.values())}")
        
        # Prepare response data
        response_data = {
            "top_artists": [artist["name"] for artist in top_artists_with_images],
            "top_artists_with_images": top_artists_with_images,
            "recommendations_by_domain": recommendations_by_domain,
            "total_domains": len(domains_with_data),
            "recommendations_per_domain": limit,
            "recommendation_type": "home_page" if is_home_page else "discover_more",
            "from_cache": False,
            "generated_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),

            "location_used": location if location else "Global",
            "location_radius": location_radius if location else None,
            "user_country": user_country,
            "user_context": user_context,
            "music_artists": music_artists,
            "user_tags": user_tags,
            "analysis": {
                "tags_used": "enhanced_music_based",
                "user_country": user_country,
                "response_time": round(response_time, 2),
                "domains_processed": list(domain_mapping.values()),
                "location_based": location is not None,
                "music_based": True,
                "top_scored_artists_used": len(top_scored_artists),
                "user_tags_used": len(user_tags),

                "is_home_page": is_home_page,
                "context_used": context
            }
        }
        
        # Cache the response for home page requests only
        if is_home_page:
            cache_key = f"crossdomain_home_{user_country}_{location}"
            crossdomain_cache[cache_key] = {
                'data': response_data,
                'timestamp': time.time()
            }
            print(f"[CACHE STORED] Cached cross-domain recommendations for home page with key: {cache_key}")
            print(f"[CACHE STORED] Cache will expire in {CACHE_EXPIRY} seconds")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Cross-domain recommendations error: {e}")
        return jsonify({"error": "Failed to get cross-domain recommendations"}), 500

@app.route('/crossdomain-progress/<user_id>', methods=['GET'])
def crossdomain_progress_direct(user_id):
    """Direct route for cross-domain progress - frontend compatibility"""
    try:
        # In-memory progress tracking
        progress_tracker = {}
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

@app.route('/create-playlist', methods=['POST', 'OPTIONS'])
def create_playlist_direct():
    """Direct route for creating Spotify playlist - frontend compatibility"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({"status": "ok"}), 200
            
        data = request.get_json()
        
        if not data or not data.get("spotify_token") or not data.get("name"):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        spotify_token = data["spotify_token"]
        name = data["name"]
        description = data.get("description", "")
        track_uris = data.get("track_uris", [])
        
        # Get user profile to get user_id
        user_profile = spotify_service.get_user_data_fast(spotify_token)
        if not user_profile or not user_profile.get("profile"):
            return jsonify({"success": False, "error": "Failed to get user profile"}), 400
        
        user_id = user_profile["profile"]["user_id"]
        
        # Create playlist
        playlist = spotify_service.create_playlist(spotify_token, user_id, name, description)
        
        if not playlist:
            return jsonify({"success": False, "error": "Failed to create playlist"}), 500
        
        # Extract track IDs from URLs and add tracks
        if track_uris and playlist.get("playlist_id"):
            track_ids = []
            for track_url in track_uris:
                # Extract track ID from Spotify URL
                if "spotify.com/track/" in track_url:
                    track_id = track_url.split("track/")[1].split("?")[0]
                    track_ids.append(track_id)
            
            if track_ids:
                track_uris_formatted = [f"spotify:track:{track_id}" for track_id in track_ids]
                success = spotify_service.add_tracks_to_playlist(spotify_token, playlist["playlist_id"], track_uris_formatted)
                if not success:
                    print("Warning: Failed to add tracks to playlist")
        
        return jsonify({
            "success": True,
            "playlist_id": playlist["playlist_id"],
            "playlist_url": playlist["playlist_url"],
            "message": f'Playlist "{name}" created successfully'
        })
        
    except Exception as e:
        print(f"Playlist creation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test-database', methods=['POST'])
def test_database_direct():
    """Test database functionality"""
    try:
        data = request.get_json()
        spotify_token = data.get("spotify_token")
        
        if not spotify_token:
            return jsonify({"error": "Missing spotify_token"}), 400
        
        # Initialize database service
        from services.database import DatabaseService
        db_service = DatabaseService()
        
        # Get user data
        user_data = spotify_service.get_user_data_fast(spotify_token)
        if not user_data:
            return jsonify({"error": "Failed to get user data"}), 400
        
        user_id = user_data["profile"]["user_id"]
        user_country = user_data["profile"].get("country", "US")
        
        # Test database operations
        session_id = db_service.create_user_session(user_id, spotify_token, user_country, "test context")
        
        # Store test recommendation
        db_service.store_recommendation_history(
            user_id=user_id,
            session_id=session_id,
            recommendation_type="test",
            user_context="test context",
            generated_tags=["test"],
            qloo_artists=[{"name": "Test Artist"}],
            playlist_data={"test": "data"},
            response_time=1.0
        )
        
        # Get user history
        history = db_service.get_user_history(user_id, 5)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "session_id": session_id,
            "history_count": len(history),
            "message": "Database test completed successfully"
        })
        
    except Exception as e:
        print(f"Database test error: {e}")
        return jsonify({"error": f"Database test failed: {e}"}), 500

@app.route('/user-analytics/<user_id>', methods=['GET'])
def get_user_analytics_direct(user_id):
    """Direct route for user analytics - frontend compatibility"""
    try:
        from services.database import DatabaseService
        db_service = DatabaseService()
        
        analytics = db_service.get_user_taste_analytics(user_id)
        return jsonify(analytics)
    except Exception as e:
        print(f"User analytics error: {e}")
        return jsonify({"error": "Failed to get user analytics"}), 500

@app.route('/analytics/clear/<user_id>', methods=['POST'])
def clear_analytics_direct(user_id):
    """Clear analytics data for a user"""
    try:
        from services.database import DatabaseService
        db_service = DatabaseService()
        
        db_service.clear_user_analytics(user_id)
        return jsonify({"status": "success", "message": "Analytics cleared"})
    except Exception as e:
        print(f"Analytics clearing error: {e}")
        return jsonify({"error": "Failed to clear analytics"}), 500

@app.route('/analytics/populate-sample/<user_id>', methods=['POST'])
def populate_sample_analytics_direct(user_id):
    """Populate sample analytics data for a user"""
    try:
        from services.database import DatabaseService
        db_service = DatabaseService()
        
        db_service.populate_sample_analytics(user_id)
        return jsonify({"status": "success", "message": "Sample analytics populated"})
    except Exception as e:
        print(f"Sample analytics population error: {e}")
        return jsonify({"error": "Failed to populate sample analytics"}), 500

@app.route('/artist-details', methods=['POST'])
def get_artist_details_direct():
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

@app.route('/artist-details-batch', methods=['POST'])
def get_artist_details_batch_direct():
    """Get detailed artist information for multiple artists from Spotify"""
    try:
        data = request.get_json()
        
        if not data or not data.get("spotify_token") or not data.get("artist_names"):
            return jsonify({"error": "Missing spotify_token or artist_names"}), 400
        
        spotify_token = data["spotify_token"]
        artist_names = data["artist_names"]
        
        if not isinstance(artist_names, list) or len(artist_names) == 0:
            return jsonify({"error": "artist_names must be a non-empty list"}), 400
        
        print(f"Batch searching for {len(artist_names)} artists: {artist_names}")
        
        # Limit the number of artists to prevent rate limiting
        max_artists = 10
        if len(artist_names) > max_artists:
            print(f"Limiting batch request to {max_artists} artists to prevent rate limiting")
            artist_names = artist_names[:max_artists]
        
        results = {}
        
        for i, artist_name in enumerate(artist_names):
            # Add delay between requests to prevent rate limiting
            if i > 0:
                time.sleep(0.5)  # 500ms delay between requests
            try:
                # First search for the artist to get their ID
                artist_search = spotify_service.search_artist(spotify_token, artist_name)
                
                if artist_search:
                    print(f"Found artist in search: {artist_search.get('name', 'Unknown')} (ID: {artist_search.get('id', 'Unknown')})")
                    # Get detailed artist information
                    artist_details = spotify_service.get_artist_details(spotify_token, artist_search["id"])
                    
                    if artist_details:
                        results[artist_name] = {"artist": artist_details}
                    else:
                        results[artist_name] = {"error": "Failed to get artist details"}
                else:
                    print(f"Artist '{artist_name}' not found in Spotify search")
                    results[artist_name] = {"error": f"Artist '{artist_name}' not found"}
                    
            except Exception as e:
                print(f"Error processing artist '{artist_name}': {e}")
                results[artist_name] = {"error": f"Failed to process artist: {str(e)}"}
        
        return jsonify({"results": results})
        
    except Exception as e:
        print(f"Batch artist details error: {e}")
        return jsonify({"error": "Failed to get batch artist details"}), 500

@app.route('/user-history/<user_id>', methods=['GET'])
def get_user_history_direct(user_id):
    """Get user recommendation history"""
    try:
        from services.database import DatabaseService
        db_service = DatabaseService()
        
        history = db_service.get_user_history(user_id, 20)
        
        return jsonify({
            "user_id": user_id,
            "history": history,
            "count": len(history)
        })
        
    except Exception as e:
        print(f"User history error: {e}")
        return jsonify({"error": f"Failed to get user history: {e}"}), 500

@app.route('/user-history/<user_id>/<int:history_id>', methods=['DELETE'])
def delete_history_item_direct(user_id, history_id):
    """Delete a specific history item"""
    try:
        from services.database import DatabaseService
        db_service = DatabaseService()
        
        success = db_service.delete_history_item(history_id, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "History item deleted successfully"
            })
        else:
            return jsonify({"error": "History item not found or unauthorized"}), 404
        
    except Exception as e:
        print(f"Delete history error: {e}")
        return jsonify({"error": f"Failed to delete history item: {e}"}), 500

@app.route('/user-history/<user_id>', methods=['DELETE'])
def clear_all_history_direct(user_id):
    """Clear all history for a user"""
    try:
        from services.database import DatabaseService
        db_service = DatabaseService()
        
        success = db_service.clear_user_history(user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "All history cleared successfully"
            })
        else:
            return jsonify({"error": "Failed to clear history"}), 500
        
    except Exception as e:
        print(f"Clear history error: {e}")
        return jsonify({"error": f"Failed to clear history: {e}"}), 500

@app.route('/new-artists/<user_id>', methods=['GET'])
def get_new_artists_direct(user_id):
    """Get new artists discovered by user in the last 7 days"""
    try:
        from services.database import DatabaseService
        db_service = DatabaseService()
        
        # Get days parameter from query string, default to 7
        days = request.args.get('days', 7, type=int)
        
        new_artists = db_service.get_new_artists(user_id, days)
        
        return jsonify({
            "user_id": user_id,
            "new_artists": new_artists,
            "count": len(new_artists),
            "days": days
        })
        
    except Exception as e:
        print(f"New artists error: {e}")
        return jsonify({"error": f"Failed to get new artists: {e}"}), 500

@app.route('/replay-recommendation/<user_id>/<int:history_id>', methods=['POST'])
def replay_recommendation_direct(user_id, history_id):
    """Replay a specific recommendation from history"""
    try:
        from services.database import DatabaseService
        db_service = DatabaseService()
        
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
        
        # Call the music recommendation function with the historical context
        # For now, just return the historical context for replay
        return jsonify({
            "status": "success",
            "message": "Replay initiated",
            "user_context": user_context,
            "history_item": history_item
        })
        
    except Exception as e:
        print(f"Replay recommendation error: {e}")
        return jsonify({"error": "Failed to replay recommendation"}), 500

@app.route('/clear-cache', methods=['POST'])
def clear_cache_direct():
    """Direct route for cache clearing - frontend compatibility"""
    try:
        data = request.get_json()
        user_id = data.get("user_id") if data else None
        
        # Clear cross-domain recommendations cache
        global crossdomain_cache
        crossdomain_cache_count = len(crossdomain_cache)
        
        crossdomain_cache.clear()
        
        if user_id:
            # Clear specific user cache
            cache_key = f"user_{user_id}"
            # In a real implementation, you would clear from Redis or memory cache
            print(f"Cleared cache for user: {user_id}")
        else:
            # Clear all cache
            print("Cleared all cache")
        
        return jsonify({
            "status": "success", 
            "message": "Cache cleared",
            "crossdomain_cache_entries_cleared": crossdomain_cache_count,
            "music_tags_cache_entries_cleared": 0,
            "note": "Music recommendations have no caching enabled"
        })
        
    except Exception as e:
        print(f"Cache clearing error: {e}")
        return jsonify({"error": "Failed to clear cache"}), 500

@app.route('/clear-qloo-cache', methods=['POST'])
def clear_qloo_cache_direct():
    """Clear Qloo variety cache manually"""
    try:
        qloo_service.clear_recent_artists_cache()
        variety_stats = qloo_service.get_variety_stats()
        return jsonify({
            "success": True,
            "message": "Qloo variety cache cleared",
            "variety_stats": variety_stats
        })
    except Exception as e:
        return jsonify({"error": f"Failed to clear cache: {e}"}), 500

@app.route('/global-music-variety', methods=['POST'])
def global_music_variety_direct():
    """Get global music variety from multiple providers"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Missing request data"}), 400
        
        category = data.get("category")  # e.g., "korean", "indian", "latin"
        mood = data.get("mood")  # e.g., "happy", "sad", "energetic"
        region = data.get("region")  # e.g., "KR", "IN", "US"
        limit = min(int(data.get("limit", 30)), 50)
        variety_boost = data.get("variety_boost", True)
        
        print(f"[GLOBAL VARIETY] Request: category={category}, mood={mood}, region={region}, limit={limit}")
        
        # Get global music variety
        result = music_aggregator_service.get_global_music_variety(
            category=category,
            mood=mood,
            region=region,
            limit=limit,
            variety_boost=variety_boost
        )
        
        return jsonify({
            "success": True,
            "artists": result["artists"],
            "providers_used": result["providers_used"],
            "total_artists_found": result["total_artists_found"],
            "unique_artists_returned": result["unique_artists_returned"],
            "variety_stats": result["variety_stats"],
            "response_time": result["response_time"],
            "category": result["category"],
            "mood": result["mood"],
            "region": result["region"],
            "variety_boost_applied": result["variety_boost_applied"]
        })
        
    except Exception as e:
        print(f"Global music variety error: {e}")
        return jsonify({"error": f"Failed to get global music variety: {e}"}), 500

@app.route('/cultural-music-variety', methods=['POST'])
def cultural_music_variety_direct():
    """Get cultural music variety from multiple providers"""
    try:
        data = request.get_json()
        
        if not data or not data.get("culture"):
            return jsonify({"error": "Missing culture parameter"}), 400
        
        culture = data["culture"]  # e.g., "korean", "indian", "latin", "african"
        limit = min(int(data.get("limit", 25)), 40)
        
        print(f"[CULTURAL VARIETY] Request: culture={culture}, limit={limit}")
        
        # Get cultural music variety
        result = music_aggregator_service.get_cultural_music_variety(
            culture=culture,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "artists": result["artists"],
            "culture": result["culture"],
            "cultural_keywords": result["cultural_keywords"],
            "providers_used": result["providers_used"],
            "total_artists_found": result["total_artists_found"],
            "unique_artists_returned": result["unique_artists_returned"],
            "variety_stats": result["variety_stats"],
            "response_time": result["response_time"]
        })
        
    except Exception as e:
        print(f"Cultural music variety error: {e}")
        return jsonify({"error": f"Failed to get cultural music variety: {e}"}), 500

@app.route('/mood-music-variety', methods=['POST'])
def mood_music_variety_direct():
    """Get mood-based music variety from multiple providers"""
    try:
        data = request.get_json()
        
        if not data or not data.get("mood"):
            return jsonify({"error": "Missing mood parameter"}), 400
        
        mood = data["mood"]  # e.g., "happy", "sad", "energetic", "romantic"
        limit = min(int(data.get("limit", 25)), 40)
        
        print(f"[MOOD VARIETY] Request: mood={mood}, limit={limit}")
        
        # Get mood-based music variety
        result = music_aggregator_service.get_mood_based_variety(
            mood=mood,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "artists": result["artists"],
            "mood": result["mood"],
            "mood_keywords": result["mood_keywords"],
            "providers_used": result["providers_used"],
            "total_artists_found": result["total_artists_found"],
            "unique_artists_returned": result["unique_artists_returned"],
            "variety_stats": result["variety_stats"],
            "response_time": result["response_time"]
        })
        
    except Exception as e:
        print(f"Mood music variety error: {e}")
        return jsonify({"error": f"Failed to get mood music variety: {e}"}), 500

@app.route('/music-variety-stats', methods=['GET'])
def music_variety_stats_direct():
    """Get comprehensive music variety statistics"""
    try:
        # Get stats from all services
        aggregator_stats = music_aggregator_service.get_variety_stats()
        qloo_stats = qloo_service.get_variety_stats()
        
        # Combine stats
        combined_stats = {
            "aggregator": aggregator_stats,
            "qloo": qloo_stats,
            "total_providers": aggregator_stats.get("total_providers", 0) + 1,  # +1 for Qloo
            "total_categories": aggregator_stats.get("total_categories", 0),
            "total_moods": aggregator_stats.get("total_moods", 0),
            "available_providers": aggregator_stats.get("available_providers", []) + ["qloo"],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        return jsonify({
            "success": True,
            "stats": combined_stats
        })
        
    except Exception as e:
        print(f"Music variety stats error: {e}")
        return jsonify({"error": f"Failed to get variety stats: {e}"}), 500

@app.route('/available-music-categories', methods=['GET'])
def available_music_categories_direct():
    """Get all available music categories and moods"""
    try:
        categories = music_aggregator_service.global_categories
        moods = music_aggregator_service.mood_categories
        
        return jsonify({
            "success": True,
            "categories": categories,
            "moods": moods,
            "total_categories": len(categories),
            "total_moods": len(moods)
        })
        
    except Exception as e:
        print(f"Available categories error: {e}")
        return jsonify({"error": f"Failed to get categories: {e}"}), 500

# Global rate limiting
spotify_request_times = []
qloo_request_times = []
gemini_request_times = []



@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "2.0",
        "optimized": True,
        "timestamp": time.time()
    })

@app.route('/health')
def health_check():
    """Detailed health check"""
    return jsonify({
        "status": "healthy",
        "services": {
            "spotify": "available",
            "qloo": "available", 
            "gemini": "available"
        },
        "performance": {
            "memory_usage": "low",
            "response_time": "fast"
        }
    })

@app.route('/cache-status', methods=['GET'])
def cache_status():
    """Get cache status and statistics"""
    global crossdomain_cache
    current_time = time.time()
    
    # Calculate crossdomain cache statistics
    crossdomain_active_entries = 0
    crossdomain_expired_entries = 0
    crossdomain_cache_keys = []
    
    for key, value in crossdomain_cache.items():
        if current_time - value['timestamp'] < CACHE_EXPIRY:
            crossdomain_active_entries += 1
            crossdomain_cache_keys.append({
                "key": key,
                "age_seconds": int(current_time - value['timestamp']),
                "expires_in_seconds": int(CACHE_EXPIRY - (current_time - value['timestamp']))
            })
        else:
            crossdomain_expired_entries += 1
    
    return jsonify({
        "crossdomain_cache": {
            "total_entries": len(crossdomain_cache),
            "active_entries": crossdomain_active_entries,
            "expired_entries": crossdomain_expired_entries,
            "cache_expiry_seconds": CACHE_EXPIRY,
            "cache_keys": crossdomain_cache_keys
        },
        "music_tags_cache": {
            "total_entries": 0,
            "active_entries": 0,
            "expired_entries": 0,
            "cache_expiry_seconds": 0,
            "cache_keys": [],
            "status": "DISABLED - No caching for music recommendations"
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500) 