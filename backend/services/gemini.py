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
        - primary_mood: string (happy, sad, energetic, calm, romantic, etc.)
        - activity_type: string (workout, study, party, relaxation, etc.)
        - energy_level: string (high, medium, low)
        - confidence: float (0.0 to 1.0)

        User context: {user_context}

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
        
        # Analyze user's cultural context from artists
        cultural_context = self._analyze_cultural_context_from_artists(user_artists, user_country)
        
        # Debug logging
        print(f"[CULTURAL DEBUG] User Country: {user_country}, Cultural Context: {cultural_context}, Artists: {user_artists}")
        
        # Generate Qloo-optimized prompt
        model = self.models["tag_generation"]
        base_url = self.base_urls[model]
        prompt = f"""
        You are an expert at generating tags for Qloo's entertainment recommendation API. 
        Generate exactly 8 tags that will work perfectly with Qloo's database.
        
        Context: {context}
        User Country: {user_country or 'Global'}
        Cultural Context: {cultural_context}
        
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

    def generate_domain_specific_tags(self, domain: str, context: str = "") -> List[str]:
        """Generate domain-specific tags that are proven to work with Qloo"""
        
        # Domain-specific tag mappings based on Qloo's database
        domain_tags = {
            "movie": {
                "romantic": ["romantic", "drama", "love", "passionate", "emotional"],
                "action": ["thriller", "adventure", "action", "exciting", "energetic"],
                "comedy": ["comedy", "funny", "humorous", "lighthearted", "upbeat"],
                "drama": ["drama", "emotional", "serious", "intense", "powerful"],
                "mystery": ["mystery", "thriller", "suspense", "intriguing", "dark"],
                "family": ["family", "heartwarming", "feel-good", "wholesome", "uplifting"]
            },
            "tv_show": {
                "romantic": ["romantic", "drama", "love", "passionate", "emotional"],
                "action": ["thriller", "adventure", "action", "exciting", "energetic"],
                "comedy": ["comedy", "funny", "humorous", "lighthearted", "upbeat"],
                "drama": ["drama", "emotional", "serious", "intense", "powerful"],
                "mystery": ["mystery", "thriller", "suspense", "intriguing", "dark"],
                "reality": ["reality", "drama", "entertaining", "popular", "trending"]
            },
            "podcast": {
                "educational": ["educational", "informative", "knowledge", "learning", "insightful"],
                "comedy": ["comedy", "funny", "humorous", "entertaining", "lighthearted"],
                "news": ["news", "current_events", "politics", "informative", "serious"],
                "business": ["business", "entrepreneurship", "success", "motivational", "professional"],
                "health": ["health", "wellness", "fitness", "lifestyle", "self_improvement"],
                "true_crime": ["true_crime", "mystery", "thriller", "suspense", "dark"]
            },
            "book": {
                "romance": ["romance", "romantic", "love", "passionate", "emotional"],
                "mystery": ["mystery", "thriller", "suspense", "detective", "crime"],
                "fantasy": ["fantasy", "adventure", "magical", "epic", "imaginative"],
                "self_help": ["self_help", "motivational", "inspirational", "personal_growth", "success"],
                "biography": ["biography", "memoir", "inspirational", "real_life", "success"],
                "fiction": ["fiction", "drama", "emotional", "compelling", "engaging"]
            },
            "artist": {
                "pop": ["pop", "mainstream", "popular", "upbeat", "catchy"],
                "rock": ["rock", "energetic", "powerful", "guitar", "band"],
                "hip_hop": ["hip_hop", "rap", "urban", "rhythm", "beats"],
                "electronic": ["electronic", "dance", "techno", "synth", "beats"],
                "jazz": ["jazz", "smooth", "sophisticated", "instrumental", "classy"],
                "classical": ["classical", "orchestral", "sophisticated", "elegant", "timeless"]
            }
        }
        
        # Get tags for the specific domain
        if domain in domain_tags:
            # Enhanced context analysis with randomization
            context_lower = context.lower()
            available_categories = list(domain_tags[domain].keys())
            
            # Try to match context to specific categories
            matched_category = None
            
            if any(word in context_lower for word in ['romantic', 'love', 'passionate', 'emotional']):
                matched_category = "romantic" if "romantic" in available_categories else None
            elif any(word in context_lower for word in ['action', 'thriller', 'exciting', 'energetic']):
                matched_category = "action" if "action" in available_categories else None
            elif any(word in context_lower for word in ['comedy', 'funny', 'humorous', 'lighthearted']):
                matched_category = "comedy" if "comedy" in available_categories else None
            elif any(word in context_lower for word in ['mystery', 'suspense', 'dark', 'thriller']):
                matched_category = "mystery" if "mystery" in available_categories else None
            elif any(word in context_lower for word in ['family', 'wholesome', 'uplifting']):
                matched_category = "family" if "family" in available_categories else None
            elif any(word in context_lower for word in ['educational', 'learning', 'knowledge']):
                matched_category = "educational" if "educational" in available_categories else None
            elif any(word in context_lower for word in ['business', 'professional', 'success']):
                matched_category = "business" if "business" in available_categories else None
            elif any(word in context_lower for word in ['health', 'wellness', 'fitness']):
                matched_category = "health" if "health" in available_categories else None
            elif any(word in context_lower for word in ['pop', 'mainstream', 'popular']):
                matched_category = "pop" if "pop" in available_categories else None
            elif any(word in context_lower for word in ['rock', 'energetic', 'powerful']):
                matched_category = "rock" if "rock" in available_categories else None
            elif any(word in context_lower for word in ['hip_hop', 'rap', 'urban']):
                matched_category = "hip_hop" if "hip_hop" in available_categories else None
            elif any(word in context_lower for word in ['electronic', 'dance', 'techno']):
                matched_category = "electronic" if "electronic" in available_categories else None
            elif any(word in context_lower for word in ['jazz', 'smooth', 'sophisticated']):
                matched_category = "jazz" if "jazz" in available_categories else None
            elif any(word in context_lower for word in ['classical', 'orchestral', 'elegant']):
                matched_category = "classical" if "classical" in available_categories else None
            
            # If no specific match, use randomization to avoid always returning the same category
            if matched_category is None:
                import random
                # Use timestamp-based randomization to ensure variety across requests
                random.seed(int(time.time() * 1000) % 10000)  # Use milliseconds for more variety
                matched_category = random.choice(available_categories)
            
            return domain_tags[domain][matched_category][:5]  # Return exactly 5 tags
        
        # Fallback to general tags with randomization
        import random
        fallback_tags = ["drama", "romantic", "adventure", "comedy", "mystery", "thriller", "action", "emotional"]
        random.shuffle(fallback_tags)
        return fallback_tags[:5]
    
    def generate_genre_based_tags(self, artist_genres: List[str], context: str = "", user_country: str = None, domain: str = "artist") -> List[str]:
        """Generate domain-specific tags based on artist genres - limit to 5 most relevant"""
        
        # Extract unique genres from user's artists
        unique_genres = list(set(artist_genres))
        print(f"Extracted genres from user artists: {unique_genres}")
        
        # Simple, proven working tags for each domain
        proven_working_tags = {
            "movie": ["drama", "romantic", "action", "comedy", "family"],
            "tv_show": ["drama", "romantic", "comedy", "family", "reality"],
            "podcast": ["entertainment", "interviews", "music", "cultural", "lifestyle"],
            "book": ["romance", "drama", "fiction", "cultural", "contemporary"],
            "artist": ["pop", "mainstream", "indian", "cultural", "contemporary"]
        }
        
        # Get the proven tags for this domain
        domain_tags = proven_working_tags.get(domain, ["drama", "romantic", "cultural"])
        
        # Add some context-based tags
        context_tags = []
        if "romantic" in context.lower() or "love" in context.lower():
            context_tags.extend(["romantic", "drama"])
        if "action" in context.lower() or "energetic" in context.lower():
            context_tags.extend(["action", "adventure"])
        if "cultural" in context.lower() or "traditional" in context.lower():
            context_tags.extend(["cultural", "traditional"])
        
        # Add cultural tags based on user country
        cultural_tags = []
        if user_country and ("india" in user_country.lower() or "indian" in user_country.lower()):
            cultural_tags.extend(["indian", "south asian"])
        elif user_country and ("american" in user_country.lower() or "usa" in user_country.lower()):
            cultural_tags.extend(["american", "western"])
        
        # Combine all tags and remove duplicates
        all_tags = domain_tags + context_tags + cultural_tags
        unique_tags = list(dict.fromkeys(all_tags))  # Preserve order while removing duplicates
        
        # Limit to 5 tags
        final_tags = unique_tags[:5]
        
        print(f"Domain {domain} - Selected {len(final_tags)} most relevant tags: {final_tags}")
        return final_tags
        proven_working_tags = {
            "movie": ["drama", "romantic", "action", "comedy", "family"],
            "tv_show": ["drama", "romantic", "comedy", "family", "reality"],
            "podcast": ["entertainment", "interviews", "music", "cultural", "lifestyle"],
            "book": ["romance", "drama", "fiction", "cultural", "contemporary"],
            "artist": ["pop", "mainstream", "indian", "cultural", "contemporary"]
        }
        
        # If we have less than 3 tags, use proven working tags
        if len(unique_search_terms) < 3:
            unique_search_terms = proven_working_tags.get(domain, ["drama", "romantic", "cultural", "entertainment", "contemporary"])
        
        print(f"Domain {domain} - Selected 5 most relevant tags: {unique_search_terms}")
        
        return unique_search_terms
    
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
    
    def generate_cultural_context(self, user_country: str, location: str = None) -> Dict:
        """Generate cultural context for recommendations"""
        try:
            # Debug: Print country detection in cultural context
            print(f"[CULTURAL DEBUG] Generating cultural context for country: {user_country}")
            
            # Simple cultural context based on country and location
            cultural_context = {
                "region": "global",
                "language_preference": "any",
                "cultural_elements": [],
                "popular_genres": []
            }
            
            if user_country == "IN":
                cultural_context.update({
                    "region": "south_asia",
                    "language_preference": "hindi",
                    "cultural_elements": ["bollywood", "indian", "desi", "hindi", "punjabi", "bhangra", "cultural", "romantic", "drama"],
                    "popular_genres": ["bollywood", "hindi_pop", "punjabi", "bhangra", "romantic", "drama"]
                })
            elif user_country in ["US", "CA", "GB", "AU"]:
                cultural_context.update({
                    "region": "western",
                    "language_preference": "english",
                    "cultural_elements": ["western", "pop", "rock", "hip_hop", "electronic", "cultural", "romantic", "drama"],
                    "popular_genres": ["pop", "rock", "hip_hop", "electronic", "romantic", "drama"]
                })
            elif user_country in ["JP", "KR"]:
                cultural_context.update({
                    "region": "east_asia",
                    "language_preference": "local",
                    "cultural_elements": ["k_pop", "j_pop", "anime", "cultural", "romantic", "drama"],
                    "popular_genres": ["k_pop", "j_pop", "anime", "j_rock", "romantic", "drama"]
                })
            
            if location:
                cultural_context["location"] = location
            else:
                # Add default location based on country for better cultural context
                if user_country == "IN":
                    cultural_context["location"] = "Mumbai"
                elif user_country == "US":
                    cultural_context["location"] = "New York"
                elif user_country == "GB":
                    cultural_context["location"] = "London"
                elif user_country == "CA":
                    cultural_context["location"] = "Toronto"
                elif user_country == "AU":
                    cultural_context["location"] = "Sydney"
                elif user_country == "JP":
                    cultural_context["location"] = "Tokyo"
                elif user_country == "KR":
                    cultural_context["location"] = "Seoul"
            
            # Debug: Print final cultural context
            print(f"[CULTURAL DEBUG] Final cultural context: {cultural_context}")
            
            return cultural_context
            
        except Exception as e:
            print(f"Error generating cultural context: {e}")
            return {
                "region": "global",
                "language_preference": "any",
                "cultural_elements": [],
                "popular_genres": []
            }
    
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
    
    def generate_enhanced_tags(self, user_context: str, user_country: str, location: str = None) -> List[str]:
        """Generate enhanced tags using Gemini with cultural context"""
        try:
            # Create enhanced prompt with cultural context
            cultural_context = self.generate_cultural_context(user_country, location)
            
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
        return self.generate_optimized_tags(user_context, user_country)
    
    def generate_music_based_cross_domain_tags(self, user_tags: List[str], artists: List[str], user_context: str, user_country: str, domain: str) -> List[str]:
        """Generate cross-domain tags based on music recommendation data"""
        try:
            # Debug: Print country detection
            print(f"[COUNTRY DEBUG] Cross-domain tags - User Country: {user_country}, Domain: {domain}")
            
            # Create enhanced prompt for cross-domain recommendations
            cultural_context = self.generate_cultural_context(user_country)
            
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
        
        return fallback_tags[:5]
    
    def filter_and_rank_tags_for_music(self, tags: List[str], user_context: str, user_country: str, location: str = None) -> List[str]:
        """Filter and rank tags for music recommendations - MUSIC ONLY with Qloo integration"""
        try:
            if not tags:
                return []
            
            # Debug: Print country detection
            print(f"[COUNTRY DEBUG] Music tags - User Country: {user_country}")
            
            # Generate cultural context for better Qloo integration
            cultural_context = self.generate_cultural_context(user_country)
            
            # Debug: Print cultural context
            print(f"[CULTURAL DEBUG] Music - Cultural Context: {cultural_context}")
            
            # First, filter out non-music tags
            music_only_tags = []
            non_music_tags = ['drama', 'family', 'cultural', 'emotional', 'romantic', 'action', 'comedy', 'thriller', 'horror', 'documentary']
            
            for tag in tags:
                tag_lower = tag.lower()
                # Skip media/non-music tags
                if tag_lower in non_music_tags:
                    continue
                # Include music-related tags
                if any(music_word in tag_lower for music_word in ['pop', 'rock', 'hip', 'rap', 'electronic', 'jazz', 'classical', 'country', 'folk', 'indie', 'alternative', 'r&b', 'soul', 'funk', 'reggae', 'latin', 'k-pop', 'j-pop', 'bollywood', 'hindi', 'punjabi', 'bhangra', 'energetic', 'upbeat', 'dance', 'party', 'chill', 'relax', 'energetic', 'happy', 'sad', 'romantic', 'nostalgic']):
                    music_only_tags.append(tag)
            
            # If we have music tags, use them
            if music_only_tags:
                tags_to_filter = music_only_tags
            else:
                # Generate music-specific tags if none found
                music_only_tags = self.generate_music_specific_tags(user_context, user_country)
                tags_to_filter = music_only_tags
            
            # Create enhanced prompt for music-specific tag filtering with Qloo integration
            prompt = f"""
            Based on this music recommendation data:
            - User context: "{user_context}"
            - User country: {user_country}
            - Cultural context: {cultural_context}
            - Location: {location if location else 'Global'}
            
            From this list of MUSIC tags: {', '.join(tags_to_filter)}
            
            Select the 5 most relevant tags for Qloo music recommendations that match the user's taste.
            Consider:
            1. Music genre relevance (pop, rock, hip-hop, electronic, etc.)
            2. Musical mood/energy (upbeat, chill, energetic, romantic, etc.)
            3. Cultural music styles (bollywood, k-pop, latin, etc.)
            4. Popularity in the region
            5. Qloo's proven tag database compatibility
            
            IMPORTANT: Only select MUSIC-related tags (genres, moods, styles).
            DO NOT select media tags like drama, family, cultural, etc.
            
            Return only the 5 selected MUSIC tags as a comma-separated list, no explanations.
            """
            
            response = self._call_gemini(prompt)
            if response:
                # Parse filtered tags
                filtered_tags = [tag.strip() for tag in response.split(",") if tag.strip()]
                # Double-check: filter out any non-music tags that might have slipped through
                final_tags = []
                for tag in filtered_tags:
                    tag_lower = tag.lower()
                    if tag_lower not in non_music_tags and any(music_word in tag_lower for music_word in ['pop', 'rock', 'hip', 'rap', 'electronic', 'jazz', 'classical', 'country', 'folk', 'indie', 'alternative', 'r&b', 'soul', 'funk', 'reggae', 'latin', 'k-pop', 'j-pop', 'bollywood', 'hindi', 'punjabi', 'bhangra', 'energetic', 'upbeat', 'dance', 'party', 'chill', 'relax', 'energetic', 'happy', 'sad', 'romantic', 'nostalgic']):
                        final_tags.append(tag)
                
                return final_tags[:5]  # Ensure max 5 tags
            
        except Exception as e:
            print(f"Error filtering music tags: {e}")
        
        # Fallback: return music-specific tags
        return self._generate_music_specific_fallback_tags(user_context, user_country)
    
    def generate_music_specific_tags(self, user_context: str, user_country: str) -> List[str]:
        """Generate music-specific tags using Gemini with Qloo integration"""
        try:
            # Debug: Print country detection
            print(f"[COUNTRY DEBUG] Generate music tags - User Country: {user_country}")
            
            # Generate cultural context for better Qloo integration
            cultural_context = self.generate_cultural_context(user_country)
            
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
                
                return music_tags[:5]  # Ensure max 5 tags
            
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
            return unique_tags[:5]
            
        except Exception as e:
            print(f"Error generating music-specific fallback tags: {e}")
            return ['pop', 'upbeat', 'mainstream', 'energetic', 'contemporary']
    
    def ai_sort_by_relevance(self, entities: List[Dict], user_artists: List[Dict], 
                           user_genres: List[List[str]], context_type: str, user_country: str, 
                           location: str = None, user_preferences: Dict = None, user_context: str = None) -> List[Dict]:
        """AI-powered sorting of entities by relevance to user preferences"""
        if not entities:
            return []
        
        try:
            # Prepare user artist names for context
            user_artist_names = [artist.get('name', '') for artist in user_artists if artist.get('name')]
            user_genre_names = []
            for genre_list in user_genres:
                user_genre_names.extend(genre_list)
            
            # Create prompt for AI sorting
            prompt = f"""
            Sort these {len(entities)} entities by relevance to a user with these preferences:
            
            User Artists: {', '.join(user_artist_names[:5])}
            User Genres: {', '.join(user_genre_names[:5])}
            User Country: {user_country}
            Context: {context_type}
            User Context: {user_context or 'general'}
            
            Entities to sort:
            {[entity.get('name', 'Unknown') for entity in entities[:10]]}
            
            Return ONLY a JSON array with the entity names in order of relevance (most relevant first).
            Example: ["Entity 1", "Entity 2", "Entity 3"]
            """
            
            response = self._call_gemini(prompt)
            if response:
                try:
                    # Extract JSON from response
                    import json
                    json_start = response.find('[')
                    json_end = response.rfind(']') + 1
                    if json_start != -1 and json_end != 0:
                        sorted_names = json.loads(response[json_start:json_end])
                        
                        # Reorder entities based on AI sorting
                        sorted_entities = []
                        for name in sorted_names:
                            for entity in entities:
                                if entity.get('name', '').lower() == name.lower():
                                    sorted_entities.append(entity)
                                    break
                        
                        # Add any remaining entities that weren't in the AI response
                        for entity in entities:
                            if entity not in sorted_entities:
                                sorted_entities.append(entity)
                        
                        return sorted_entities
                except Exception as e:
                    print(f"Error parsing AI sorting response: {e}")
            
        except Exception as e:
            print(f"Error in AI sorting: {e}")
        
        # Fallback: return original order
        return entities

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
            
            return None
            
        except Exception as e:
            print(f"Error calling enhanced Gemini API: {e}")
            return None

    def _analyze_cultural_context_from_artists(self, user_artists: List[str], user_country: str = None) -> str:
        """Analyze cultural context from user's favorite artists"""
        if not user_artists:
            return "global"
        
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
        artist_names_lower = [artist.lower() for artist in user_artists]
        
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
                "CA": "western",
                "AU": "western"
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
        
        return validated_tags[:8]  # Limit to 8 tags

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

    def _generate_qloo_fallback_tags(self, context: str, user_country: str, cultural_context: str, qloo_proven_tags: Dict) -> List[str]:
        """Generate fallback tags when AI generation fails"""
        fallback_tags = []
        
        # Add cultural context tags
        if cultural_context != "global":
            cultural_tags = qloo_proven_tags.get("cultural", [])
            fallback_tags.extend(cultural_tags[:2])
        
        # Add mood tags based on context
        context_lower = context.lower()
        if any(word in context_lower for word in ["happy", "upbeat", "energetic", "party"]):
            mood_tags = qloo_proven_tags.get("mood", [])
            fallback_tags.extend([tag for tag in mood_tags if "happy" in tag.lower() or "energetic" in tag.lower()][:2])
        elif any(word in context_lower for word in ["sad", "melancholic", "emotional"]):
            mood_tags = qloo_proven_tags.get("mood", [])
            fallback_tags.extend([tag for tag in mood_tags if "emotional" in tag.lower() or "drama" in tag.lower()][:2])
        elif any(word in context_lower for word in ["romantic", "love", "passionate"]):
            mood_tags = qloo_proven_tags.get("mood", [])
            fallback_tags.extend([tag for tag in mood_tags if "romantic" in tag.lower() or "love" in tag.lower()][:2])
        
        # Add genre tags
        genre_tags = qloo_proven_tags.get("genre", [])
        fallback_tags.extend(genre_tags[:2])
        
        # Add activity tags
        activity_tags = qloo_proven_tags.get("activity", [])
        fallback_tags.extend(activity_tags[:2])
        
        return list(set(fallback_tags))[:8]  # Remove duplicates and limit
    
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
        return potential_tags[:5] if potential_tags else ["pop", "energetic", "upbeat", "mainstream", "popular"]
    
    def _generate_fallback_tags(self, context: str, user_country: str = None) -> list:
        import random
        import time
        enhanced_tags = [
            "romantic", "drama", "comedy", "thriller", "adventure",
            "sad", "happy", "energetic", "calm", "upbeat",
            "emotional", "nostalgic", "party", "workout", "study",
            "mystery", "inspirational", "relaxation", "motivational",
            "pop", "mainstream", "cultural", "contemporary", "indian",
            "alternative", "indie", "rock", "electronic", "jazz",
            "classical", "folk", "country", "blues", "soul",
            "r&b", "hip_hop", "reggae", "latin", "world",
            "ambient", "chill", "lounge", "acoustic", "instrumental",
            "action", "suspense", "family", "reality", "educational",
            "informative", "knowledge", "learning", "insightful",
            "business", "entrepreneurship", "success", "professional",
            "health", "wellness", "fitness", "lifestyle", "self_improvement",
            "true_crime", "detective", "crime", "fantasy", "magical",
            "epic", "imaginative", "personal_growth", "biography", "memoir",
            "real_life", "fiction", "compelling", "engaging", "powerful",
            "guitar", "band", "rap", "urban", "rhythm", "beats",
            "dance", "techno", "synth", "smooth", "sophisticated",
            "instrumental", "classy", "timeless", "orchestral", "elegant"
        ]
        random.seed(hash(context + str(int(time.time() * 1000) % 10000)))
        context_lower = context.lower()
        if any(word in context_lower for word in ['happy', 'joy', 'excited', 'party', 'celebration']):
            base_tags = ["happy", "upbeat", "energetic", "party", "celebration", "pop", "mainstream", "contemporary"]
            additional_tags = random.sample([tag for tag in enhanced_tags if tag not in base_tags], 2)
            return base_tags[:6] + additional_tags
        elif any(word in context_lower for word in ['sad', 'melancholy', 'crying', 'emotional']):
            base_tags = ["sad", "emotional", "melancholic", "nostalgic", "ballad", "drama", "romantic", "cultural"]
            additional_tags = random.sample([tag for tag in enhanced_tags if tag not in base_tags], 2)
            return base_tags[:6] + additional_tags
        elif any(word in context_lower for word in ['romantic', 'love', 'passionate', 'intimate']):
            base_tags = ["romantic", "love", "passionate", "intimate", "ballad", "emotional", "drama", "cultural"]
            additional_tags = random.sample([tag for tag in enhanced_tags if tag not in base_tags], 2)
            return base_tags[:6] + additional_tags
        elif any(word in context_lower for word in ['workout', 'gym', 'running', 'fitness']):
            base_tags = ["energetic", "workout", "high_energy", "motivational", "upbeat", "pop", "mainstream", "contemporary"]
            additional_tags = random.sample([tag for tag in enhanced_tags if tag not in base_tags], 2)
            return base_tags[:6] + additional_tags
        elif any(word in context_lower for word in ['study', 'work', 'focus', 'concentration']):
            base_tags = ["calm", "ambient", "study", "focus", "relaxation", "emotional", "cultural", "contemporary"]
            additional_tags = random.sample([tag for tag in enhanced_tags if tag not in base_tags], 2)
            return base_tags[:6] + additional_tags
        elif any(word in context_lower for word in ['explore', 'discover', 'diverse', 'variety']):
            return random.sample(enhanced_tags, 8)
        else:
            base_tags = ["drama", "romantic", "adventure", "comedy", "mystery", "pop", "mainstream", "cultural"]
            num_replacements = random.randint(2, 3)
            replacement_tags = random.sample([tag for tag in enhanced_tags if tag not in base_tags], num_replacements)
            return base_tags[:8-num_replacements] + replacement_tags