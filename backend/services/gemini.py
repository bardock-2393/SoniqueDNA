import requests
import json
import time
from typing import Dict, List, Optional
import os

class GeminiService:
    """Enhanced Gemini API service with model selection for different tasks"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY', "AIzaSyBNb-EtpmciV73x0VzhQdHUtaJysd4aRKM")
        # Model configurations for different tasks
        self.models = {
            "context_analysis": "gemini-2.0-flash-exp",
            "tag_generation": "gemini-2.5-flash",
            "complex_analysis": "gemini-2.5-flash",
            "creative_generation": "gemini-2.5-flash",
            "detailed_analysis": "gemini-2.5-pro"
        }
        self.base_urls = {
            "gemini-2.0-flash-exp": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent",
            "gemini-2.0-flash": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            "gemini-2.5-flash": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            "gemini-2.5-pro": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
        }
        self.base_url = self.base_urls["gemini-2.0-flash-exp"]

    def analyze_context_fast(self, user_context: str) -> Dict:
        """Fast context analysis - single Gemini call with focused prompt"""
        prompt = f"""
        Analyze this user context and return ONLY a JSON object with these exact fields:
        - primary_mood: string (happy, sad, melancholic, depressed, blue, energetic, calm, romantic, angry, anxious, nostalgic, etc.)
        - activity_type: string (workout, study, party, relaxation, introspection, social, travel, etc.)
        - energy_level: string (high, medium, low)
        - confidence: float (0.0 to 1.0)

        IMPORTANT: Pay special attention to emotional expressions:
        - "feeling blue" = sad/melancholic mood
        - "feeling down" = sad/depressed mood  
        - "feeling happy" = happy/upbeat mood
        - "feeling energetic" = high energy
        - "feeling tired" = low energy
        - "feeling romantic" = romantic mood
        - "feeling nostalgic" = nostalgic mood

        User context: "{user_context}"

        Return only the JSON object, no other text.
        """
        
        try:
            response = self._call_gemini(prompt)
            if response:
                # Try to parse JSON from response
                try:
                    # Extract JSON from response text
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start != -1 and json_end != 0:
                        json_str = response[json_start:json_end]
                        result = json.loads(json_str)
                        return result
                except json.JSONDecodeError:
                    pass
                
                # Fallback parsing
                return self._parse_context_fallback(response)
            
        except Exception as e:
            print(f"Context analysis error: {e}")
        
        # Default fallback
        return {
            "primary_mood": "neutral",
            "activity_type": "general",
            "energy_level": "medium",
            "confidence": 0.5
        }
    
    def generate_optimized_tags(self, context: str, user_country: str = None, user_artists: List[str] = None) -> list:
        """Qloo-optimized tag generation with cultural intelligence"""
        return self.generate_qloo_optimized_tags(context, user_country, user_artists)
    
    def generate_qloo_optimized_tags(self, context: str, user_country: str = None, user_artists: List[str] = None) -> List[str]:
        """Generate tags specifically optimized for Qloo API with cultural intelligence"""
        
        # Qloo-proven tag categories that work across all domains
        qloo_proven_tags = {
            "mood": ["romantic", "drama", "comedy", "thriller", "emotional", "upbeat", "calm", "energetic"],
            "genre": ["pop", "mainstream", "alternative", "indie", "classical", "jazz", "rock", "electronic"],
            "cultural": ["indian", "western", "asian", "latin", "african", "middle_eastern", "european"],
            "activity": ["party", "workout", "study", "relaxation", "travel", "social", "introspective"],
            "style": ["contemporary", "traditional", "modern", "vintage", "experimental", "mainstream"],
            "audience": ["family", "adult", "teen", "children", "senior", "young_adult"],
            "theme": ["love", "friendship", "adventure", "mystery", "inspiration", "nostalgia"],
            "energy": ["high_energy", "low_energy", "moderate", "intense", "gentle", "powerful"]
        }
        
        # Generate comprehensive cultural context using Gemini
        cultural_context = self.generate_cultural_context(user_country, user_artists=user_artists)
        
        # Debug logging
        print(f"[CULTURAL DEBUG] User Country: {user_country}, Cultural Context: {cultural_context}, Artists: {user_artists}")
        
        # Get Qloo artist tags from cultural context
        qloo_artist_tags = cultural_context.get("qloo_artist_tags", [])
        
        # Generate Qloo-optimized prompt
        model = self.models["tag_generation"]
        base_url = self.base_urls[model]
        prompt = f"""
        You are an expert at generating tags for Qloo's entertainment recommendation API. 
        Generate exactly 8 tags that will work perfectly with Qloo's database.
        
        Context: {context}
        User Country: {user_country or 'Global'}
        Cultural Context: {cultural_context}
        Qloo Artist Tags: {qloo_artist_tags}
        
        IMPORTANT QLOO REQUIREMENTS:
        1. Use ONLY tags that exist in Qloo's database
        2. Mix different categories: mood, genre, cultural, activity, style
        3. Include cultural tags based on user's music taste
        4. Ensure tags work across movies, TV shows, podcasts, books, and music
        5. Use proven Qloo tags from these categories:
           - Mood: romantic, drama, comedy, thriller, emotional, upbeat, calm, energetic
           - Genre: pop, mainstream, alternative, indie, classical, jazz, rock, electronic
           - Cultural: indian, western, asian, latin, african, middle_eastern, european
           - Activity: party, workout, study, relaxation, travel, social, introspective
           - Style: contemporary, traditional, modern, vintage, experimental, mainstream
           - Audience: family, adult, teen, children, senior, young_adult
           - Theme: love, friendship, adventure, mystery, inspiration, nostalgia
           - Energy: high_energy, low_energy, moderate, intense, gentle, powerful
        
        CRITICAL SORTING REQUIREMENT:
        - The FIRST tag must be the MOST RELEVANT tag for the user's context
        - This tag will be used for primary sorting of recommendations
        - Choose the tag that best represents the user's current taste and context
        
        CULTURAL INTELLIGENCE:
        - Use the provided Qloo Artist Tags: {qloo_artist_tags}
        - If user listens to Hindi artists: include "indian", "cultural", "bollywood"
        - If user listens to K-pop: include "asian", "korean", "pop"
        - If user listens to Latin music: include "latin", "spanish", "cultural"
        - If user listens to Western pop: include "western", "mainstream", "pop"
        
        Return ONLY a JSON array of 8 strings, no other text.
        Example: ["indian", "romantic", "cultural", "emotional", "contemporary", "mainstream", "upbeat", "family"]
        """
        
        try:
            response = self._call_gemini_enhanced(prompt, model, base_url)
            if response:
                try:
                    json_start = response.find('[')
                    json_end = response.rfind(']') + 1
                    if json_start != -1 and json_end != 0:
                        json_str = response[json_start:json_end]
                        result = json.loads(json_str)
                        if isinstance(result, list) and len(result) == 8:
                            # Validate tags against Qloo-proven list
                            validated_tags = self._validate_tags_for_qloo(result, qloo_proven_tags)
                            print(f"[TAG DEBUG] Generated tags: {result}, Validated tags: {validated_tags}")
                            return validated_tags
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"Qloo-optimized tag generation error: {e}")
        
        # Fallback with cultural intelligence
        fallback_tags = self._generate_qloo_fallback_tags(context, user_country, cultural_context, qloo_proven_tags)
        print(f"[FALLBACK DEBUG] Using fallback tags: {fallback_tags}")
        return fallback_tags


    

    
    def analyze_artist_context(self, artist_name: str, context: str) -> Dict:
        """Analyze artist in context - single focused call"""
        prompt = f"""
        Analyze this artist in the given context and return a JSON object:
        - mood_match: float (0.0 to 1.0) - how well artist matches context mood
        - energy_match: float (0.0 to 1.0) - how well artist matches context energy
        - relevance_score: float (0.0 to 1.0) - overall relevance to context
        
        Artist: {artist_name}
        Context: {context}
        
        Return only the JSON object.
        """
        
        try:
            response = self._call_gemini(prompt)
            if response:
                try:
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start != -1 and json_end != 0:
                        json_str = response[json_start:json_end]
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
        except Exception as e:
            print(f"Artist analysis error: {e}")
        
        # Default fallback
        return {
            "mood_match": 0.5,
            "energy_match": 0.5,
            "relevance_score": 0.5
        }
    
    def generate_cultural_context(self, user_country: str, location: str = None, user_artists: List[str] = None) -> Dict:
        """Generate cultural context for recommendations using Gemini AI"""
        try:
            # Debug: Print country detection in cultural context
            print(f"[CULTURAL DEBUG] Generating cultural context for country: {user_country}")
            
            # Handle user_artists - extract names if they're dictionaries
            artist_names = []
            if user_artists:
                for artist in user_artists:
                    if isinstance(artist, dict):
                        # Extract name from dictionary
                        artist_name = artist.get('name', str(artist))
                        artist_names.append(artist_name)
                    elif isinstance(artist, str):
                        artist_names.append(artist)
                    else:
                        artist_names.append(str(artist))
            
            # Create a comprehensive prompt for Gemini to analyze cultural context
            prompt = f"""
            Analyze the cultural context for music recommendations based on:
            - User country: {user_country}
            - Location: {location or 'Not specified'}
            - User artists: {', '.join(artist_names) if artist_names else 'Not specified'}
            
            Generate a JSON object with these exact fields:
            - region: string (south_asia, east_asia, western, latin_america, africa, middle_east, europe, global)
            - language_preference: string (hindi, english, korean, japanese, spanish, portuguese, arabic, french, german, any)
            - cultural_elements: array of strings (cultural tags that work with Qloo API)
            - popular_genres: array of strings (music genres popular in this region)
            - qloo_artist_tags: array of strings (Qloo-compatible tags for artist recommendations)
            - cultural_significance: float (0.0 to 1.0, how culturally specific this context is)
            
            IMPORTANT QLOO TAG REQUIREMENTS:
            - Use only tags that exist in Qloo's database
            - For artists, focus on: pop, rock, hip_hop, electronic, jazz, classical, country, folk, indie, alternative, r&b, soul, funk, reggae, latin, k-pop, j-pop, bollywood, hindi, punjabi, bhangra, mainstream, contemporary, traditional, experimental
            - Cultural tags should be: indian, western, asian, latin, african, middle_eastern, european, korean, japanese, desi, hispanic, arabic, turkish, persian
            - Mood tags should be: romantic, drama, comedy, thriller, emotional, upbeat, calm, energetic, sad, happy, nostalgic, passionate, introspective
            
            EXAMPLES:
            - India (IN): {{"region": "south_asia", "language_preference": "hindi", "cultural_elements": ["bollywood", "indian", "desi", "hindi", "punjabi", "bhangra"], "popular_genres": ["bollywood", "hindi_pop", "punjabi", "bhangra"], "qloo_artist_tags": ["bollywood", "indian", "hindi", "punjabi", "cultural", "romantic", "drama", "mainstream"], "cultural_significance": 0.9}}
            - USA (US): {{"region": "western", "language_preference": "english", "cultural_elements": ["western", "pop", "rock", "hip_hop"], "popular_genres": ["pop", "rock", "hip_hop", "electronic"], "qloo_artist_tags": ["pop", "rock", "hip_hop", "mainstream", "contemporary", "western", "romantic", "drama"], "cultural_significance": 0.7}}
            - Korea (KR): {{"region": "east_asia", "language_preference": "korean", "cultural_elements": ["k_pop", "korean", "asian"], "popular_genres": ["k_pop", "j_pop", "anime", "j_rock"], "qloo_artist_tags": ["k_pop", "j_pop", "asian", "pop", "mainstream", "contemporary", "romantic", "drama"], "cultural_significance": 0.8}}
            
            Return only the JSON object, no other text.
            """
            
            # Use Gemini to generate cultural context
            print(f"[CULTURAL DEBUG] Calling Gemini API for cultural context...")
            response = self._call_gemini(prompt)
            if response:
                print(f"[CULTURAL DEBUG] Gemini response received: {response[:200]}...")
                try:
                    # Extract JSON from response
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start != -1 and json_end != 0:
                        json_str = response[json_start:json_end]
                        cultural_context = json.loads(json_str)
                        
                        # Validate and enhance the response
                        cultural_context = self._validate_cultural_context(cultural_context, user_country, location, user_artists)
                        
                        # Debug: Print final cultural context
                        print(f"[CULTURAL DEBUG] Gemini-generated cultural context: {cultural_context}")
                        
                        return cultural_context
                        
                except json.JSONDecodeError as e:
                    print(f"[CULTURAL DEBUG] JSON parsing error: {e}")
                    print(f"[CULTURAL DEBUG] Raw response: {response}")
                    pass
            else:
                print(f"[CULTURAL DEBUG] No response from Gemini API")
            
        except Exception as e:
            print(f"Error generating cultural context with Gemini: {e}")
        
        # Fallback to enhanced hardcoded context with Qloo artist tags
        return self._generate_fallback_cultural_context(user_country, location, user_artists)
    
    def _validate_cultural_context(self, cultural_context: Dict, user_country: str, location: str, user_artists: List[str]) -> Dict:
        """Validate and enhance the Gemini-generated cultural context"""
        
        # Ensure all required fields exist
        required_fields = ["region", "language_preference", "cultural_elements", "popular_genres", "qloo_artist_tags", "cultural_significance"]
        for field in required_fields:
            if field not in cultural_context:
                cultural_context[field] = self._get_default_cultural_field(field, user_country)
        
        # Validate qloo_artist_tags - ensure they're Qloo-compatible
        qloo_artist_tags = cultural_context.get("qloo_artist_tags", [])
        validated_tags = self._validate_qloo_artist_tags(qloo_artist_tags)
        cultural_context["qloo_artist_tags"] = validated_tags
        
        # Add location if provided
        if location:
            cultural_context["location"] = location
        else:
            # Add default location based on country
            cultural_context["location"] = self._get_default_location(user_country)
        
        # Add artist analysis if available
        if user_artists:
            artist_cultural_analysis = self._analyze_artists_cultural_context(user_artists)
            cultural_context["artist_cultural_analysis"] = artist_cultural_analysis
        
        return cultural_context
    
    def _validate_qloo_artist_tags(self, tags: List[str]) -> List[str]:
        """Validate tags to ensure they're compatible with Qloo's artist tag database"""
        
        # Qloo-proven artist tags that work across all regions
        qloo_proven_artist_tags = [
            # Genres
            "pop", "rock", "hip_hop", "electronic", "jazz", "classical", "country", "folk", "indie", "alternative", "r&b", "soul", "funk", "reggae", "latin", "k_pop", "j_pop", "bollywood", "hindi", "punjabi", "bhangra",
            # Cultural
            "indian", "western", "asian", "latin", "african", "middle_eastern", "european", "korean", "japanese", "desi", "hispanic", "arabic", "turkish", "persian",
            # Mood/Style
            "romantic", "drama", "comedy", "thriller", "emotional", "upbeat", "calm", "energetic", "sad", "happy", "nostalgic", "passionate", "introspective",
            # Other
            "mainstream", "contemporary", "traditional", "experimental", "cultural"
        ]
        
        validated_tags = []
        for tag in tags:
            tag_lower = tag.lower()
            # Check if tag is in proven list
            if tag_lower in [t.lower() for t in qloo_proven_artist_tags]:
                validated_tags.append(tag)
            else:
                # Try to find closest match
                closest_tag = self._find_closest_qloo_tag(tag_lower, qloo_proven_artist_tags)
                if closest_tag:
                    validated_tags.append(closest_tag)
        
        # Ensure we have at least some tags
        if not validated_tags:
            validated_tags = ["mainstream", "pop", "contemporary", "romantic", "drama"]
        
        return validated_tags[:8]  # Limit to 8 tags
    
    def _find_closest_qloo_tag(self, tag: str, proven_tags: List[str]) -> str:
        """Find the closest proven Qloo tag using simple string matching"""
        if not proven_tags:
            return ""
        
        best_match = ""
        best_score = 0
        
        for proven_tag in proven_tags:
            proven_lower = proven_tag.lower()
            
            # Exact match
            if tag == proven_lower:
                return proven_tag
            
            # Contains match
            if tag in proven_lower or proven_lower in tag:
                score = len(set(tag) & set(proven_lower)) / len(set(tag) | set(proven_lower))
                if score > best_score:
                    best_score = score
                    best_match = proven_tag
        
        # Return best match if similarity is above threshold
        if best_score > 0.3:
            return best_match
        
        return ""
    
    def _analyze_artists_cultural_context(self, user_artists: List[str]) -> Dict:
        """Analyze cultural context from user's favorite artists"""
        if not user_artists:
            return {"detected_culture": "global", "confidence": 0.0}
        
        # Handle user_artists - extract names if they're dictionaries
        artist_names = []
        for artist in user_artists:
            if isinstance(artist, dict):
                # Extract name from dictionary
                artist_name = artist.get('name', str(artist))
                artist_names.append(artist_name)
            elif isinstance(artist, str):
                artist_names.append(artist)
            else:
                artist_names.append(str(artist))
        
        # Cultural keywords for different regions
        cultural_keywords = {
            "indian": ["arjit", "pritam", "shreya", "atif", "neha", "badshah", "karan", "amit", "vishal", "shankar", "bollywood", "hindi", "punjabi", "bhangra", "ghazal", "qawwali"],
            "korean": ["bts", "blackpink", "exo", "twice", "red velvet", "k-pop", "korean", "seoul"],
            "japanese": ["j-pop", "j-rock", "anime", "japanese", "tokyo", "akb48", "babymetal"],
            "latin": ["bad bunny", "j balvin", "maluma", "shakira", "reggaeton", "latin", "spanish", "mexican", "colombian", "puerto rican"],
            "african": ["afrobeats", "nigerian", "ghanaian", "south african", "african", "wizkid", "burna boy", "davido"],
            "middle_eastern": ["arabic", "turkish", "persian", "middle eastern", "egyptian", "lebanese"],
            "western": ["ed sheeran", "taylor swift", "the weeknd", "dua lipa", "post malone", "ariana grande", "british", "american", "canadian", "australian"]
        }
        
        # Count cultural matches
        cultural_counts = {}
        artist_names_lower = [artist.lower() for artist in artist_names]
        
        for culture, keywords in cultural_keywords.items():
            count = 0
            for artist in artist_names_lower:
                for keyword in keywords:
                    if keyword in artist:
                        count += 1
                        break
            cultural_counts[culture] = count
        
        # Find the most common culture
        if cultural_counts:
            max_culture = max(cultural_counts, key=cultural_counts.get)
            if cultural_counts[max_culture] > 0:
                confidence = min(cultural_counts[max_culture] / len(artist_names), 1.0)
                return {"detected_culture": max_culture, "confidence": confidence}
        
        return {"detected_culture": "global", "confidence": 0.0}
    
    def _get_default_cultural_field(self, field: str, user_country: str) -> any:
        """Get default values for cultural context fields"""
        defaults = {
            "region": "global",
            "language_preference": "any",
            "cultural_elements": [],
            "popular_genres": [],
            "qloo_artist_tags": ["mainstream", "pop", "contemporary", "romantic", "drama"],
            "cultural_significance": 0.5
        }
        
        # Override based on country
        if user_country == "IN":
            defaults.update({
                "region": "south_asia",
                "language_preference": "hindi",
                "cultural_elements": ["bollywood", "indian", "desi", "hindi", "punjabi", "bhangra"],
                "popular_genres": ["bollywood", "hindi_pop", "punjabi", "bhangra"],
                "qloo_artist_tags": ["bollywood", "indian", "hindi", "punjabi", "cultural", "romantic", "drama", "mainstream"],
                "cultural_significance": 0.9
            })
        elif user_country in ["US", "CA", "GB", "AU"]:
            defaults.update({
                "region": "western",
                "language_preference": "english",
                "cultural_elements": ["western", "pop", "rock", "hip_hop", "electronic"],
                "popular_genres": ["pop", "rock", "hip_hop", "electronic"],
                "qloo_artist_tags": ["pop", "rock", "hip_hop", "mainstream", "contemporary", "western", "romantic", "drama"],
                "cultural_significance": 0.7
            })
        elif user_country in ["JP", "KR"]:
            defaults.update({
                "region": "east_asia",
                "language_preference": "local",
                "cultural_elements": ["k_pop", "j_pop", "anime", "asian"],
                "popular_genres": ["k_pop", "j_pop", "anime", "j_rock"],
                "qloo_artist_tags": ["k_pop", "j_pop", "asian", "pop", "mainstream", "contemporary", "romantic", "drama"],
                "cultural_significance": 0.8
            })
        
        return defaults.get(field, defaults["region"])
    
    def _get_default_location(self, user_country: str) -> str:
        """Get default location based on country"""
        location_map = {
            "IN": "Mumbai",
            "US": "New York",
            "GB": "London",
            "CA": "Toronto",
            "AU": "Sydney",
            "JP": "Tokyo",
            "KR": "Seoul",
            "MX": "Mexico City",
            "BR": "São Paulo",
            "AR": "Buenos Aires",
            "CO": "Bogotá",
            "NG": "Lagos",
            "GH": "Accra",
            "ZA": "Johannesburg",
            "EG": "Cairo",
            "TR": "Istanbul",
            "IR": "Tehran"
        }
        return location_map.get(user_country, "Global")
    
    def _generate_fallback_cultural_context(self, user_country: str, location: str, user_artists: List[str]) -> Dict:
        """Generate fallback cultural context when Gemini fails"""
        print(f"[CULTURAL DEBUG] Using fallback cultural context for country: {user_country}")
        
        # Start with default context
        cultural_context = {
            "region": "global",
            "language_preference": "any",
            "cultural_elements": [],
            "popular_genres": [],
            "qloo_artist_tags": ["mainstream", "pop", "contemporary", "romantic", "drama"],
            "cultural_significance": 0.5
        }
        
        # Enhance based on country
        if user_country == "IN":
            cultural_context.update({
                "region": "south_asia",
                "language_preference": "hindi",
                "cultural_elements": ["bollywood", "indian", "desi", "hindi", "punjabi", "bhangra", "cultural", "romantic", "drama"],
                "popular_genres": ["bollywood", "hindi_pop", "punjabi", "bhangra", "romantic", "drama"],
                "qloo_artist_tags": ["bollywood", "indian", "hindi", "punjabi", "cultural", "romantic", "drama", "mainstream"],
                "cultural_significance": 0.9
            })
        elif user_country in ["US", "CA", "GB", "AU"]:
            cultural_context.update({
                "region": "western",
                "language_preference": "english",
                "cultural_elements": ["western", "pop", "rock", "hip_hop", "electronic", "cultural", "romantic", "drama"],
                "popular_genres": ["pop", "rock", "hip_hop", "electronic", "romantic", "drama"],
                "qloo_artist_tags": ["pop", "rock", "hip_hop", "mainstream", "contemporary", "western", "romantic", "drama"],
                "cultural_significance": 0.7
            })
        elif user_country in ["JP", "KR"]:
            cultural_context.update({
                "region": "east_asia",
                "language_preference": "local",
                "cultural_elements": ["k_pop", "j_pop", "anime", "cultural", "romantic", "drama"],
                "popular_genres": ["k_pop", "j_pop", "anime", "j_rock", "romantic", "drama"],
                "qloo_artist_tags": ["k_pop", "j_pop", "asian", "pop", "mainstream", "contemporary", "romantic", "drama"],
                "cultural_significance": 0.8
            })
        
        # Add location
        if location:
            cultural_context["location"] = location
        else:
            cultural_context["location"] = self._get_default_location(user_country)
        
        # Add artist analysis if available
        if user_artists:
            artist_cultural_analysis = self._analyze_artists_cultural_context(user_artists)
            cultural_context["artist_cultural_analysis"] = artist_cultural_analysis
        
        print(f"[CULTURAL DEBUG] Fallback cultural context: {cultural_context}")
        return cultural_context
    
    def enhance_context_detection(self, user_context: str, user_country: str) -> Dict:
        """Enhanced context detection with mood and language preference"""
        try:
            # Analyze context for mood and activity
            context_analysis = self.analyze_context_fast(user_context)
            
            # Determine language preference based on country
            language_preference = {"primary_language": "any"}
            if user_country == "IN":
                language_preference = {"primary_language": "hindi"}
            elif user_country in ["US", "CA", "GB", "AU"]:
                language_preference = {"primary_language": "english"}
            
            # Determine context type
            context_type = "general"
            context_lower = user_context.lower()
            
            if any(word in context_lower for word in ['sad', 'melancholy', 'crying', 'heartbreak']):
                context_type = "sad"
            elif any(word in context_lower for word in ['happy', 'joy', 'excited', 'party']):
                context_type = "upbeat"
            elif any(word in context_lower for word in ['romantic', 'love', 'passionate']):
                context_type = "romantic"
            elif any(word in context_lower for word in ['workout', 'gym', 'running', 'exercise']):
                context_type = "energetic"
            elif any(word in context_lower for word in ['study', 'work', 'focus', 'concentration']):
                context_type = "calm"
            
            return {
                "context_type": context_type,
                "language_preference": language_preference,
                "mood_preference": {
                    "primary_mood": context_analysis.get("primary_mood", "neutral"),
                    "activity_type": context_analysis.get("activity_type", "general"),
                    "energy_level": context_analysis.get("energy_level", "medium")
                }
            }
            
        except Exception as e:
            print(f"Error in enhanced context detection: {e}")
            return {
                "context_type": "general",
                "language_preference": {"primary_language": "any"},
                "mood_preference": {
                    "primary_mood": "neutral",
                    "activity_type": "general",
                    "energy_level": "medium"
                }
            }
    
    def generate_enhanced_tags(self, user_context: str, user_country: str, location: str = None, user_artists: List[str] = None) -> List[str]:
        """Generate enhanced tags using Gemini with cultural context"""
        try:
            # Create enhanced prompt with cultural context
            cultural_context = self.generate_cultural_context(user_country, location, user_artists)
            
            prompt = f"""
            Based on this user context: "{user_context}"
            And cultural context: {cultural_context}
            
            Generate 8-12 music-related tags that would be useful for finding similar artists and tracks.
            Consider:
            1. The user's mood and activity
            2. Cultural preferences for {user_country}
            3. Popular music styles in their region
            4. Emotional and thematic elements
            
            Return only a comma-separated list of tags, no explanations.
            Examples: upbeat, energetic, romantic, sad, bollywood, pop, rock, electronic, etc.
            """
            
            response = self._call_gemini(prompt)
            if response:
                # Parse tags from response
                tags = [tag.strip() for tag in response.split(",") if tag.strip()]
                return tags[:12]  # Limit to 12 tags
            
        except Exception as e:
            print(f"Error generating enhanced tags: {e}")
        
        # Fallback to simple tags
        return self.generate_optimized_tags(user_context, user_country, user_artists)
    
    def generate_music_based_cross_domain_tags(self, user_tags: List[str], artists: List[str], user_context: str, user_country: str, domain: str) -> List[str]:
        """Generate cross-domain tags based on music recommendation data"""
        try:
            # Debug: Print country detection
            print(f"[COUNTRY DEBUG] Cross-domain tags - User Country: {user_country}, Domain: {domain}")
            
            # Create enhanced prompt for cross-domain recommendations
            cultural_context = self.generate_cultural_context(user_country, user_artists=artists)
            
            # Debug: Print cultural context
            print(f"[CULTURAL DEBUG] Cross-domain - Cultural Context: {cultural_context}")
            
            prompt = f"""
            Based on this music recommendation data:
            - User context: "{user_context}"
            - User tags: {', '.join(user_tags) if user_tags else 'none'}
            - Similar artists: {', '.join(artists) if artists else 'none'}
            - Target domain: {domain}
            - User country: {user_country}
            - Cultural context: {cultural_context}
            
            Generate 6-10 tags for {domain} recommendations that match the user's music taste.
            Consider:
            1. The emotional and thematic elements from the music
            2. Cultural preferences for {user_country}
            3. Similarities between music and {domain} content
            4. Popular {domain} styles that match the music vibe
            
            Return only a comma-separated list of tags, no explanations.
            Examples for {domain}: action, drama, comedy, thriller, romance, documentary, etc.
            """
            
            response = self._call_gemini(prompt)
            if response:
                # Parse tags from response
                tags = [tag.strip() for tag in response.split(",") if tag.strip()]
                return tags[:10]  # Limit to 10 tags
            
        except Exception as e:
            print(f"Error generating music-based cross-domain tags: {e}")
        
        # Enhanced fallback with randomization to prevent same results
        import random
        
        # Add some variety based on the domain and context
        context_lower = user_context.lower()
        
        # Create domain-specific fallback tags with randomization
        fallback_tags = []
        
        if domain == "movie":
            all_movie_tags = [
                "drama", "romantic", "action", "comedy", "thriller",
                "adventure", "mystery", "crime", "family", "suspense",
                "love", "emotional", "exciting", "funny", "dark",
                "romance", "entertaining", "popular", "classic", "modern",
                "sci_fi", "horror", "animation", "documentary", "biography",
                "war", "western", "musical", "fantasy", "historical",
                "indie", "foreign", "art_house", "experimental", "cult"
            ]
        elif domain == "tv_show":
            all_tv_tags = [
                "drama", "romantic", "comedy", "reality", "thriller",
                "action", "mystery", "crime", "family", "suspense",
                "love", "emotional", "exciting", "funny", "dark",
                "romance", "entertaining", "popular", "classic", "modern",
                "sci_fi", "horror", "animation", "documentary", "biography",
                "war", "western", "musical", "fantasy", "historical",
                "indie", "foreign", "art_house", "experimental", "cult",
                "sitcom", "soap_opera", "game_show", "talk_show", "news"
            ]
        elif domain == "podcast":
            all_podcast_tags = [
                "educational", "informative", "knowledge", "learning", "insightful",
                "comedy", "funny", "humorous", "entertaining", "lighthearted",
                "news", "current_events", "politics", "serious", "informative",
                "business", "entrepreneurship", "success", "motivational", "professional",
                "health", "wellness", "fitness", "lifestyle", "self_improvement"
            ]
        elif domain == "book":
            all_book_tags = [
                "romance", "romantic", "love", "passionate", "emotional",
                "mystery", "thriller", "suspense", "detective", "crime",
                "fantasy", "adventure", "magical", "epic", "imaginative",
                "self_help", "motivational", "inspirational", "personal_growth", "success",
                "fiction", "drama", "compelling", "engaging", "emotional"
            ]
        elif domain == "artist":
            all_artist_tags = [
                "pop", "mainstream", "popular", "upbeat", "catchy",
                "rock", "energetic", "powerful", "guitar", "band",
                "hip_hop", "rap", "urban", "rhythm", "beats",
                "electronic", "dance", "techno", "synth", "beats",
                "jazz", "smooth", "sophisticated", "instrumental", "classy"
            ]
        else:
            # Generic tags for unknown domains
            all_artist_tags = ["drama", "romantic", "adventure", "comedy", "mystery", "thriller", "action", "emotional"]
        
        # Use the appropriate tag list
        if domain == "movie":
            tag_pool = all_movie_tags
        elif domain == "tv_show":
            tag_pool = all_tv_tags
        elif domain == "podcast":
            tag_pool = all_podcast_tags
        elif domain == "book":
            tag_pool = all_book_tags
        elif domain == "artist":
            tag_pool = all_artist_tags
        else:
            tag_pool = all_artist_tags  # fallback
        
        # Add context-based filtering
        if any(word in context_lower for word in ['romantic', 'love', 'passionate']):
            romantic_tags = [tag for tag in tag_pool if any(word in tag for word in ['romantic', 'love', 'passionate', 'emotional'])]
            if romantic_tags:
                fallback_tags.extend(romantic_tags[:3])
        
        if any(word in context_lower for word in ['energetic', 'upbeat', 'party']):
            energetic_tags = [tag for tag in tag_pool if any(word in tag for word in ['energetic', 'upbeat', 'exciting', 'powerful'])]
            if energetic_tags:
                fallback_tags.extend(energetic_tags[:3])
        
        if any(word in context_lower for word in ['cultural', 'traditional', 'indian']):
            cultural_tags = [tag for tag in tag_pool if any(word in tag for word in ['cultural', 'traditional', 'indian'])]
            if cultural_tags:
                fallback_tags.extend(cultural_tags[:2])
        
        # Fill remaining slots with proven common tags
        remaining_slots = 5 - len(fallback_tags)
        if remaining_slots > 0:
            # Use timestamp-based randomization for variety
            random.seed(int(time.time() * 1000) % 10000)
            
            # Prioritize common, proven tags that work well with Qloo
            proven_tags = ["drama", "romantic", "comedy", "action", "thriller", "mystery", "crime", "family"]
            available_proven = [tag for tag in proven_tags if tag in tag_pool and tag not in fallback_tags]
            
            if available_proven:
                # Use proven tags first
                fallback_tags.extend(random.sample(available_proven, min(remaining_slots, len(available_proven))))
                remaining_slots = 5 - len(fallback_tags)
            
            # Fill any remaining slots with other available tags
            if remaining_slots > 0:
                available_tags = [tag for tag in tag_pool if tag not in fallback_tags]
                if available_tags:
                    # Add more randomization by shuffling the available tags
                    random.shuffle(available_tags)
                    fallback_tags.extend(random.sample(available_tags, min(remaining_slots, len(available_tags))))
        
        # Ensure we have exactly 5 tags, prioritizing proven tags
        if len(fallback_tags) < 5:
            proven_fillers = ["drama", "romantic", "comedy", "action", "thriller", "mystery", "crime", "family"]
            available_fillers = [tag for tag in proven_fillers if tag in tag_pool and tag not in fallback_tags]
            if available_fillers:
                fallback_tags.extend(random.sample(available_fillers, min(5 - len(fallback_tags), len(available_fillers))))
        
        # Final fallback to ensure 5 tags
        if len(fallback_tags) < 5:
            fallback_tags.extend(random.sample(tag_pool, 5 - len(fallback_tags)))
        
        return fallback_tags
    

    
    def generate_music_specific_tags(self, user_context: str, user_country: str) -> List[str]:
        """Generate music-specific tags using Gemini with Qloo integration"""
        try:
            # Debug: Print country detection
            print(f"[COUNTRY DEBUG] Generate music tags - User Country: {user_country}")
            
            # Generate cultural context for better Qloo integration
            cultural_context = self.generate_cultural_context(user_country, user_artists=None)
            
            # Debug: Print cultural context
            print(f"[CULTURAL DEBUG] Generate music tags - Cultural Context: {cultural_context}")
            
            # Create prompt for generating music-specific tags
            prompt = f"""
            Based on this music recommendation request:
            - User context: "{user_context}"
            - User country: {user_country}
            - Cultural context: {cultural_context}
            
            Generate 5 music-specific tags for Qloo music recommendations.
            
            Consider:
            1. Music genres (pop, rock, hip-hop, electronic, jazz, classical, country, folk, indie, alternative, r&b, soul, funk, reggae, latin, k-pop, j-pop, bollywood, hindi, punjabi, bhangra)
            2. Musical moods/energy (energetic, upbeat, dance, party, chill, relax, happy, sad, romantic, nostalgic)
            3. Cultural music styles based on the user's country
            4. Qloo's proven tag database compatibility
            
            IMPORTANT: Only generate MUSIC-related tags (genres, moods, styles).
            DO NOT generate media tags like drama, family, cultural, etc.
            
            Return only the 5 generated MUSIC tags as a comma-separated list, no explanations.
            """
            
            response = self._call_gemini(prompt)
            if response:
                # Parse generated tags
                generated_tags = [tag.strip() for tag in response.split(",") if tag.strip()]
                # Filter to ensure only music tags
                non_music_tags = ['drama', 'family', 'cultural', 'emotional', 'romantic', 'action', 'comedy', 'thriller', 'horror', 'documentary']
                music_tags = []
                for tag in generated_tags:
                    tag_lower = tag.lower()
                    if tag_lower not in non_music_tags and any(music_word in tag_lower for music_word in ['pop', 'rock', 'hip', 'rap', 'electronic', 'jazz', 'classical', 'country', 'folk', 'indie', 'alternative', 'r&b', 'soul', 'funk', 'reggae', 'latin', 'k-pop', 'j-pop', 'bollywood', 'hindi', 'punjabi', 'bhangra', 'energetic', 'upbeat', 'dance', 'party', 'chill', 'relax', 'energetic', 'happy', 'sad', 'romantic', 'nostalgic']):
                        music_tags.append(tag)
                
                return music_tags  # No limit
            
        except Exception as e:
            print(f"Error generating music-specific tags: {e}")
        
        # Fallback to the existing fallback function
        return self._generate_music_specific_fallback_tags(user_context, user_country)
    
    def _generate_music_specific_fallback_tags(self, user_context: str, user_country: str) -> List[str]:
        """Generate music-specific fallback tags based on context and country with Qloo compatibility"""
        try:
            context_lower = user_context.lower()
            country_lower = user_country.lower() if user_country else ""
            
            # Music-specific tags based on context
            if 'party' in context_lower or 'dance' in context_lower:
                base_tags = ['upbeat', 'dance', 'energetic', 'pop', 'electronic']
            elif 'workout' in context_lower or 'gym' in context_lower:
                base_tags = ['energetic', 'upbeat', 'rock', 'hip_hop', 'electronic']
            elif 'study' in context_lower or 'focus' in context_lower:
                base_tags = ['chill', 'ambient', 'classical', 'jazz', 'lofi']
            elif 'romantic' in context_lower or 'date' in context_lower:
                base_tags = ['romantic', 'r&b', 'pop', 'soul', 'jazz']
            elif 'sad' in context_lower or 'melancholic' in context_lower:
                base_tags = ['sad', 'indie', 'alternative', 'folk', 'acoustic']
            else:
                base_tags = ['pop', 'upbeat', 'mainstream', 'energetic', 'contemporary']
            
            # Add country-specific music tags
            if 'in' in country_lower or 'india' in country_lower:
                base_tags.extend(['bollywood', 'hindi', 'punjabi'])
            elif 'us' in country_lower or 'usa' in country_lower:
                base_tags.extend(['hip_hop', 'r&b', 'country'])
            elif 'kr' in country_lower or 'korea' in country_lower:
                base_tags.extend(['k_pop', 'korean'])
            elif 'jp' in country_lower or 'japan' in country_lower:
                base_tags.extend(['j_pop', 'japanese'])
            elif 'br' in country_lower or 'brazil' in country_lower:
                base_tags.extend(['latin', 'samba', 'bossa_nova'])
            
            # Return unique tags, max 5
            unique_tags = list(dict.fromkeys(base_tags))  # Preserve order while removing duplicates
            return unique_tags
            
        except Exception as e:
            print(f"Error generating music-specific fallback tags: {e}")
            return ['pop', 'upbeat', 'mainstream', 'energetic', 'contemporary']
    


    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Gemini API with error handling"""
        try:
            headers = {
                "Content-Type": "application/json",
            }
            
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                params={"key": self.api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]
                    if "parts" in content and len(content["parts"]) > 0:
                        return content["parts"][0]["text"]
                else:
                    print(f"[GEMINI DEBUG] No candidates in response: {result}")
            else:
                print(f"[GEMINI DEBUG] API error {response.status_code}: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None

    def _call_gemini_enhanced(self, prompt: str, model: str, base_url: str) -> Optional[str]:
        """Enhanced Gemini call with model selection"""
        try:
            headers = {
                "Content-Type": "application/json",
            }
            
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            response = requests.post(
                base_url,
                headers=headers,
                json=data,
                params={"key": self.api_key},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]
                    if "parts" in content and len(content["parts"]) > 0:
                        return content["parts"][0]["text"]
                else:
                    print(f"[GEMINI ENHANCED DEBUG] No candidates in response: {result}")
            else:
                print(f"[GEMINI ENHANCED DEBUG] API error {response.status_code}: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"Error calling enhanced Gemini API: {e}")
            return None

    def _analyze_cultural_context_from_artists(self, user_artists: List[str], user_country: str = None) -> str:
        """Analyze cultural context from user's favorite artists"""
        if not user_artists:
            return "global"
        
        # Handle user_artists - extract names if they're dictionaries
        artist_names = []
        for artist in user_artists:
            if isinstance(artist, dict):
                # Extract name from dictionary
                artist_name = artist.get('name', str(artist))
                artist_names.append(artist_name)
            elif isinstance(artist, str):
                artist_names.append(artist)
            else:
                artist_names.append(str(artist))
        
        # Cultural keywords for different regions
        cultural_keywords = {
            "indian": ["arjit", "pritam", "shreya", "atif", "neha", "badshah", "karan", "amit", "vishal", "shankar", "bollywood", "hindi", "punjabi", "bhangra", "ghazal", "qawwali"],
            "korean": ["bts", "blackpink", "exo", "twice", "red velvet", "k-pop", "korean", "seoul"],
            "japanese": ["j-pop", "j-rock", "anime", "japanese", "tokyo", "akb48", "babymetal"],
            "latin": ["bad bunny", "j balvin", "maluma", "shakira", "reggaeton", "latin", "spanish", "mexican", "colombian", "puerto rican"],
            "african": ["afrobeats", "nigerian", "ghanaian", "south african", "african", "wizkid", "burna boy", "davido"],
            "middle_eastern": ["arabic", "turkish", "persian", "middle eastern", "egyptian", "lebanese"],
            "western": ["ed sheeran", "taylor swift", "the weeknd", "dua lipa", "post malone", "ariana grande", "british", "american", "canadian", "australian"]
        }
        
        # Count cultural matches
        cultural_counts = {}
        artist_names_lower = [artist.lower() for artist in artist_names]
        
        for culture, keywords in cultural_keywords.items():
            count = 0
            for artist in artist_names_lower:
                for keyword in keywords:
                    if keyword in artist:
                        count += 1
                        break
            cultural_counts[culture] = count
        
        # Find the most common culture
        if cultural_counts:
            max_culture = max(cultural_counts, key=cultural_counts.get)
            if cultural_counts[max_culture] > 0:
                return max_culture
        
        # Fallback based on user country
        if user_country:
            country_culture_map = {
                "IN": "indian",
                "PK": "indian",  # Similar cultural context
                "KR": "korean",
                "JP": "japanese",
                "MX": "latin",
                "BR": "latin",
                "AR": "latin",
                "CO": "latin",
                "NG": "african",
                "GH": "african",
                "ZA": "african",
                "EG": "middle_eastern",
                "TR": "middle_eastern",
                "IR": "middle_eastern",
                "US": "western",
                "GB": "western",
                "CA": "western"
            }
            return country_culture_map.get(user_country, "global")
        
        return "global"

    def _validate_tags_for_qloo(self, tags: List[str], qloo_proven_tags: Dict) -> List[str]:
        """Validate and filter tags for Qloo compatibility"""
        validated_tags = []
        
        # Flatten all proven tags
        all_proven_tags = []
        for category, tag_list in qloo_proven_tags.items():
            all_proven_tags.extend(tag_list)
        
        for tag in tags:
            tag_lower = tag.lower()
            
            # Check if tag is already in proven list
            if tag_lower in [t.lower() for t in all_proven_tags]:
                validated_tags.append(tag)
                continue
            
            # Try to find closest match
            closest_tag = self._find_closest_proven_tag(tag_lower, all_proven_tags)
            if closest_tag:
                validated_tags.append(closest_tag)
        
        return validated_tags  # No limit

    def _find_closest_proven_tag(self, tag: str, proven_tags: List[str]) -> str:
        """Find the closest proven tag using simple string matching"""
        if not proven_tags:
            return ""
        
        # Simple similarity check
        best_match = ""
        best_score = 0
        
        for proven_tag in proven_tags:
            proven_lower = proven_tag.lower()
            
            # Exact match
            if tag == proven_lower:
                return proven_tag
            
            # Contains match
            if tag in proven_lower or proven_lower in tag:
                score = len(set(tag) & set(proven_lower)) / len(set(tag) | set(proven_lower))
                if score > best_score:
                    best_score = score
                    best_match = proven_tag
        
        # Return best match if similarity is above threshold
        if best_score > 0.3:
            return best_match
        
        return ""

    def _generate_qloo_fallback_tags(self, context: str, user_country: str, cultural_context: Dict, qloo_proven_tags: Dict) -> List[str]:
        """Generate fallback tags when AI generation fails - FIXED to use cultural context"""
        fallback_tags = []
        
        # Use Qloo artist tags from cultural context if available
        if isinstance(cultural_context, dict) and "qloo_artist_tags" in cultural_context:
            qloo_artist_tags = cultural_context.get("qloo_artist_tags", [])
            if qloo_artist_tags:
                fallback_tags.extend(qloo_artist_tags[:4])  # Use up to 4 Qloo artist tags
                print(f"[CULTURAL FALLBACK] Using Qloo artist tags: {qloo_artist_tags[:4]}")
        
        # Use cultural context if available (backward compatibility)
        elif isinstance(cultural_context, str) and cultural_context != "global" and user_country == "IN":
            # Use Indian/Bollywood specific tags
            fallback_tags.extend(["bollywood", "indian", "hindi", "punjabi"])
            print(f"[CULTURAL FALLBACK] Using Indian cultural tags: {fallback_tags}")
        
        # Add music-specific tags that work with Qloo
        music_tags = ["mainstream", "pop", "hip_hop", "electronic", "rock"]
        fallback_tags.extend(music_tags)
        
        # Add mood tags based on context
        context_lower = context.lower()
        if any(word in context_lower for word in ["happy", "upbeat", "energetic", "party"]):
            fallback_tags.extend(["energetic", "upbeat"])
        elif any(word in context_lower for word in ["sad", "melancholic", "emotional"]):
            fallback_tags.extend(["emotional", "drama"])
        elif any(word in context_lower for word in ["romantic", "love", "passionate"]):
            fallback_tags.extend(["romantic", "love"])
        
        # Remove duplicates and limit
        unique_tags = list(set(fallback_tags))
        print(f"[CULTURAL FALLBACK] Final fallback tags: {unique_tags}")
        return unique_tags
    
    def _parse_context_fallback(self, response: str) -> Dict:
        """Fallback parsing for context analysis"""
        response_lower = response.lower()
        
        # Simple keyword matching
        mood_keywords = {
            "happy": "happy", "joy": "happy", "excited": "energetic",
            "sad": "sad", "melancholy": "sad", "energetic": "energetic",
            "calm": "calm", "relaxed": "calm", "romantic": "romantic"
        }
        
        activity_keywords = {
            "workout": "workout", "exercise": "workout", "gym": "workout",
            "study": "study", "work": "work", "party": "party",
            "relax": "relaxation", "sleep": "relaxation"
        }
        
        energy_keywords = {
            "high": "high", "energetic": "high", "fast": "high",
            "medium": "medium", "moderate": "medium",
            "low": "low", "slow": "low", "calm": "low"
        }
        
        # Extract values
        primary_mood = "neutral"
        for keyword, mood in mood_keywords.items():
            if keyword in response_lower:
                primary_mood = mood
                break
        
        activity_type = "general"
        for keyword, activity in activity_keywords.items():
            if keyword in response_lower:
                activity_type = activity
                break
        
        energy_level = "medium"
        for keyword, energy in energy_keywords.items():
            if keyword in response_lower:
                energy_level = energy
                break
        
        return {
            "primary_mood": primary_mood,
            "activity_type": activity_type,
            "energy_level": energy_level,
            "confidence": 0.6
        }
    
    def _parse_tags_fallback(self, response: str) -> List[str]:
        """Fallback parsing for tag generation"""
        response_lower = response.lower()
        
        # Extract potential tags
        potential_tags = []
        
        # Common music tags
        music_tags = [
            "pop", "rock", "hip hop", "electronic", "jazz", "classical",
            "energetic", "calm", "romantic", "sad", "happy", "upbeat",
            "workout", "study", "party", "relaxation", "motivational"
        ]
        
        for tag in music_tags:
            if tag in response_lower:
                potential_tags.append(tag)
        
        # Return up to 5 tags
        return potential_tags if potential_tags else ["pop", "energetic", "upbeat", "mainstream", "popular"]
    


    def analyze_compound_context(self, user_context: str) -> Dict:
        """AI-driven analysis of compound contexts like 'anime songs for study'"""
        prompt = f"""
        Analyze this user context and extract ALL relevant elements. Return ONLY a JSON object with these exact fields:
        
        - primary_elements: array of strings (e.g., ["anime", "japanese", "soundtrack"])
        - activity_context: array of strings (e.g., ["study", "focus", "background"])
        - mood_preference: array of strings (e.g., ["calm", "instrumental", "non-distracting"])
        - genre_hints: array of strings (e.g., ["j-pop", "anime_opening", "soundtrack"])
        - energy_level: string (high, medium, low)
        - confidence: float (0.0 to 1.0)
        
        Examples:
        - "anime songs for study" → {{"primary_elements": ["anime", "japanese"], "activity_context": ["study", "focus"], "mood_preference": ["calm", "instrumental"], "genre_hints": ["j-pop", "anime_opening", "soundtrack"], "energy_level": "low", "confidence": 0.9}}
        - "bollywood party music" → {{"primary_elements": ["bollywood", "indian"], "activity_context": ["party", "dance"], "mood_preference": ["energetic", "upbeat"], "genre_hints": ["bollywood", "hindi_pop", "bhangra"], "energy_level": "high", "confidence": 0.9}}
        - "sad romantic songs" → {{"primary_elements": ["romantic", "emotional"], "activity_context": ["introspective"], "mood_preference": ["sad", "melancholy"], "genre_hints": ["romantic", "ballad"], "energy_level": "low", "confidence": 0.8}}
        
        User context: {user_context}
        
        Return only the JSON object, no other text.
        """
        
        try:
            response = self._call_gemini(prompt)
            if response:
                try:
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start != -1 and json_end != 0:
                        json_str = response[json_start:json_end]
                        result = json.loads(json_str)
                        return result
                except json.JSONDecodeError:
                    pass
                
                return self._parse_compound_context_fallback(response)
            
        except Exception as e:
            print(f"Compound context analysis error: {e}")
        
        # Default fallback
        return {
            "primary_elements": ["general"],
            "activity_context": ["general"],
            "mood_preference": ["neutral"],
            "genre_hints": ["mainstream"],
            "energy_level": "medium",
            "confidence": 0.5
        }

    def generate_context_aware_tags(self, user_context: str, user_country: str = None, user_artists: List[str] = None) -> List[str]:
        """Generate context-aware tags using dynamic AI analysis"""
        
        # Use Gemini to dynamically analyze context and generate tags
        prompt = f"""
        Analyze this user context and generate 5-8 relevant music tags for recommendations.
        
        User Context: "{user_context}"
        User Country: {user_country or 'Global'}
        
        IMPORTANT: Generate tags that are:
        1. RELEVANT to the specific content mentioned (e.g., "naruto" → anime, japanese, otaku)
        2. APPROPRIATE for music recommendations
        3. DIVERSE (mix of genres, moods, styles)
        4. CULTURALLY RELEVANT to the user's country
        
        EXAMPLES:
        - "i just watch naruto song related to it" → ["anime", "japanese", "otaku", "upbeat", "energetic"]
        - "feeling blue today" → ["melancholic", "emotional", "sad", "introspective", "drama"]
        - "romantic dinner music" → ["romantic", "love", "emotional", "calm", "drama"]
        - "workout playlist" → ["energetic", "upbeat", "workout", "dance", "powerful"]
        - "study focus music" → ["calm", "focus", "ambient", "instrumental", "relaxing"]
        
        Return ONLY a JSON array of tag strings, no other text.
        Example: ["anime", "japanese", "upbeat", "energetic", "otaku"]
        """
        
        try:
            response = self._call_gemini(prompt)
            if response:
                # Try to parse JSON from response
                try:
                    # Extract JSON array from response text
                    json_start = response.find('[')
                    json_end = response.rfind(']') + 1
                    if json_start != -1 and json_end != 0:
                        json_str = response[json_start:json_end]
                        tags = json.loads(json_str)
                        
                        # Validate tags are strings
                        if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
                            print(f"[AI TAGS] Dynamically generated {len(tags)} tags: {tags}")
                            return tags
                        
                except json.JSONDecodeError:
                    pass
                
                # Fallback parsing
                return self._parse_tags_fallback(response)
            
        except Exception as e:
            print(f"Dynamic tag generation error: {e}")
        
        # Fallback to basic analysis if dynamic generation fails
        print(f"[AI TAGS] Using fallback tag generation")
        
        # First, analyze the context for mood and emotional state
        context_analysis = self.analyze_context_fast(user_context)
        print(f"[AI CONTEXT] Fast analysis: {context_analysis}")
        
        """Generate context-aware tags using AI analysis instead of hardcoded rules"""
        
        # Analyze the compound context
        context_analysis = self.analyze_compound_context(user_context)
        print(f"[AI CONTEXT] Analysis: {context_analysis}")
        
        # Extract all relevant elements
        all_elements = []
        all_elements.extend(context_analysis.get("primary_elements", []))
        all_elements.extend(context_analysis.get("activity_context", []))
        all_elements.extend(context_analysis.get("mood_preference", []))
        all_elements.extend(context_analysis.get("genre_hints", []))
        
        # Remove duplicates and filter out empty strings
        all_elements = list(dict.fromkeys([elem for elem in all_elements if elem]))
        
        # Add cultural context if available
        if user_country:
            cultural_context = self.generate_cultural_context(user_country, user_artists=user_artists)
            cultural_elements = cultural_context.get("cultural_elements", [])
            all_elements.extend(cultural_elements[:3])  # Limit cultural elements
        
        # Remove duplicates again
        all_elements = list(dict.fromkeys(all_elements))
        
        print(f"[AI TAGS] Generated {len(all_elements)} context-aware tags: {all_elements}")
        return all_elements

    def _parse_compound_context_fallback(self, response: str) -> Dict:
        """Fallback parsing for compound context analysis"""
        response_lower = response.lower()
        
        # Simple keyword extraction as fallback
        primary_elements = []
        activity_context = []
        mood_preference = []
        genre_hints = []
        
        # Extract primary elements
        if any(word in response_lower for word in ['anime', 'japanese']):
            primary_elements.extend(['anime', 'japanese'])
        if any(word in response_lower for word in ['bollywood', 'indian']):
            primary_elements.extend(['bollywood', 'indian'])
        if any(word in response_lower for word in ['romantic', 'love']):
            primary_elements.extend(['romantic', 'love'])
        
        # Extract activity context
        if any(word in response_lower for word in ['study', 'work', 'focus']):
            activity_context.extend(['study', 'focus'])
        if any(word in response_lower for word in ['party', 'dance']):
            activity_context.extend(['party', 'dance'])
        if any(word in response_lower for word in ['workout', 'gym']):
            activity_context.extend(['workout', 'energetic'])
        
        # Extract mood preference
        if any(word in response_lower for word in ['calm', 'relax']):
            mood_preference.extend(['calm', 'relax'])
        if any(word in response_lower for word in ['energetic', 'upbeat']):
            mood_preference.extend(['energetic', 'upbeat'])
        if any(word in response_lower for word in ['sad', 'melancholy']):
            mood_preference.extend(['sad', 'melancholy'])
        
        return {
            "primary_elements": primary_elements or ["general"],
            "activity_context": activity_context or ["general"],
            "mood_preference": mood_preference or ["neutral"],
            "genre_hints": genre_hints or ["mainstream"],
            "energy_level": "medium",
            "confidence": 0.6
        }

    def filter_all_tracks_comprehensive(self, all_tracks: List[Dict], user_context: str, user_country: str, 
                                       user_artists: List[Dict] = None, user_tracks: List[Dict] = None, 
                                       context_type: str = "general", location: str = None) -> List[Dict]:
        """Comprehensive track filtering and ranking using Gemini AI"""
        try:
            if not all_tracks:
                return []
            
            # Generate cultural context for better filtering
            cultural_context = self.generate_cultural_context(user_country, location, user_artists)
            
            # Extract artist names for context
            artist_names = []
            if user_artists:
                for artist in user_artists:
                    if isinstance(artist, dict):
                        artist_names.append(artist.get('name', str(artist)))
                    else:
                        artist_names.append(str(artist))
            
            # Create comprehensive prompt for track filtering
            prompt = f"""
            Analyze and rank these {len(all_tracks)} tracks based on:
            - User context: "{user_context}"
            - User country: {user_country}
            - Context type: {context_type}
            - Cultural context: {cultural_context}
            - User artists: {', '.join(artist_names) if artist_names else 'None'}
            
            For each track, consider:
            1. Relevance to user context and mood
            2. Cultural appropriateness for {user_country}
            3. Similarity to user's favorite artists
            4. Context type match ({context_type})
            5. Overall quality and popularity
            
            Return ONLY a JSON array of track names in order of relevance (most relevant first).
            Example: ["Track Name 1", "Track Name 2", "Track Name 3", ...]
            
            Track list:
            {[track.get('name', 'Unknown') for track in all_tracks[:20]]}  # Show first 20 tracks
            """
            
            response = self._call_gemini(prompt)
            if response:
                try:
                    # Extract JSON array from response
                    json_start = response.find('[')
                    json_end = response.rfind(']') + 1
                    if json_start != -1 and json_end != 0:
                        json_str = response[json_start:json_end]
                        ranked_track_names = json.loads(json_str)
                        
                        # Reorder tracks based on Gemini ranking
                        ranked_tracks = []
                        track_name_to_track = {track.get('name', '').lower(): track for track in all_tracks}
                        
                        for track_name in ranked_track_names:
                            track_name_lower = track_name.lower()
                            if track_name_lower in track_name_to_track:
                                ranked_tracks.append(track_name_to_track[track_name_lower])
                        
                        # Add any remaining tracks that weren't ranked
                        for track in all_tracks:
                            track_name_lower = track.get('name', '').lower()
                            if track_name_lower not in [t.get('name', '').lower() for t in ranked_tracks]:
                                ranked_tracks.append(track)
                        
                        print(f"[GEMINI FILTER] Ranked {len(ranked_tracks)} tracks using AI")
                        return ranked_tracks[:30]  # Return top 30 tracks
                        
                except json.JSONDecodeError as e:
                    print(f"[GEMINI FILTER] JSON parsing error: {e}")
                    pass
            
        except Exception as e:
            print(f"[GEMINI FILTER] Error in comprehensive filtering: {e}")
        
        # Fallback: return original tracks with basic filtering
        print(f"[GEMINI FILTER] Using fallback filtering for {len(all_tracks)} tracks")
        
        # Basic cultural filtering
        filtered_tracks = []
        for track in all_tracks:
            track_name = track.get('name', '').lower()
            artist_name = track.get('artist', '').lower()
            
            # Skip tracks that don't match cultural context
            if user_country == "IN":
                # For Indian users, prioritize Indian/Bollywood content
                if any(keyword in track_name or keyword in artist_name for keyword in 
                      ['bollywood', 'hindi', 'punjabi', 'indian', 'desi']):
                    filtered_tracks.append(track)
                elif len(filtered_tracks) < 20:  # Allow some non-Indian tracks
                    filtered_tracks.append(track)
            else:
                # For other countries, include all tracks
                filtered_tracks.append(track)
        
        return filtered_tracks[:30]  # Return top 30 tracks