import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { 
  Film, 
  Tv, 
  Headphones, 
  BookOpen, 
  Music, 
  Loader2,
  ExternalLink,
  Star,
  ArrowLeft,
  Calendar,
  Clock,
  User,
  Globe,
  Award,
  Database,
  RefreshCw
} from 'lucide-react';
import { ComicText } from './magicui/comic-text';
import { crossDomainCache, cacheUtils } from '../utils/cacheManager';

interface CrossDomainRecommendationsProps {
  userContext: string;
  musicArtists: string[];
  topScoredArtists?: string[];
  userTags?: string[];
  spotifyToken: string;
  location?: string;  // Add location prop
  locationRadius?: number;  // Add location radius prop
  onClose?: () => void;
}

interface RecommendationItem {
  name: string;
  id?: string;
  description?: string;
  url?: string;
  image_url?: string;
  popularity?: number;
  affinity_score?: number;
  cultural_relevance?: number;
  tags?: string[];
  properties?: {
    // Common fields
    image?: { url?: string } | null;
    description?: string;
    year?: number;
    genre?: string;
    genres?: string[];
    language?: string;
    country?: string;
    url?: string;
    external_urls?: Record<string, string>;
    
    // Movie specific
    release_year?: number;
    release_date?: string;
    content_rating?: string;
    duration?: string;
    director?: string;
    production_companies?: string[];
    akas?: string[];
    short_descriptions?: string[];
    
    // TV Show specific
    seasons?: number;
    episodes?: number;
    websites?: string[];
    
    // Podcast specific
    rating?: string;
    channel?: string;
    host?: string;
    episode_count?: number;
    short_description?: string;
    
    // Book specific
    title?: string;
    author?: string;
    publisher?: string;
    format?: string;
    page_count?: number;
    isbn10?: string;
    isbn13?: string;
    publication_year?: number;
    
    // Artist specific
    followers?: number;
    albums?: number;
    spotify_url?: string;
    
    // Legacy fields (keeping for backward compatibility)
    runtime?: string;
  };
  
  // External links from Qloo API
  external?: {
    wikidata?: string;
    imdb?: string;
    spotify?: string;
    instagram?: string;
    twitter?: string;
    facebook?: string;
    lastfm?: string;
    musicbrainz?: string;
    goodreads?: string;
    letterboxd?: string;
    itunes?: string;
  };
  
  selected_tag?: string;
  source_artist?: string;
}

interface CrossDomainData {
  recommendations_by_domain: {
    movie: RecommendationItem[];
    'TV show': RecommendationItem[];
    podcast: RecommendationItem[];
    book: RecommendationItem[];
    'music artist': RecommendationItem[];
  };
  top_artists: string[];
  top_artists_with_images: Array<{
    id: string;
    name: string;
    image: string | null;
    genres: string[];
    popularity: number;
    followers: number;
  }>;
  detailed_results: Record<string, any>;
  total_domains: number;
  recommendations_per_domain: number;
  user_context: string;
  music_artists: string[];
  cultural_context?: string;
  location_used?: string;
  user_country?: string;
  generated_timestamp?: string;
  from_cache?: boolean;
  cache_buster?: string;
}

// Cache configuration
const CACHE_KEY = 'crossdomain_recommendations_cache';

// Generate a hash for the request parameters to use as cache key
const generateRequestHash = (
  userContext: string,
  musicArtists: string[],
  topScoredArtists: string[],
  userTags: string[],
  forceRefresh: boolean = false,
  location?: string,
  locationRadius?: number
): string => {
  const data = {
    userContext,
    musicArtists: musicArtists.sort(),
    topScoredArtists: topScoredArtists.sort(),
    userTags: userTags.sort(),
    location,
    locationRadius,
    // Add timestamp for cache busting when force refresh is used
    timestamp: forceRefresh ? Date.now() : Math.floor(Date.now() / 300000) * 300000 // 5-minute cache window
  };
  
  return btoa(JSON.stringify(data));
};

const domainConfig = {
  movie: {
    title: 'Movies',
    icon: Film,
    color: 'bg-red-500',
    hoverColor: 'hover:bg-red-600',
    description: 'Discover films that match your vibe'
  },
  'TV show': {
    title: 'TV Shows',
    icon: Tv,
    color: 'bg-blue-500',
    hoverColor: 'hover:bg-blue-600',
    description: 'Series that complement your taste'
  },
  podcast: {
    title: 'Podcasts',
    icon: Headphones,
    color: 'bg-purple-500',
    hoverColor: 'hover:bg-purple-600',
    description: 'Audio content that resonates with you'
  },
  book: {
    title: 'Books',
    icon: BookOpen,
    color: 'bg-green-500',
    hoverColor: 'hover:bg-green-600',
    description: 'Stories that align with your interests'
  },
  'music artist': {
    title: 'Music Artists',
    icon: Music,
    color: 'bg-orange-500',
    hoverColor: 'hover:bg-orange-600',
    description: 'Artists similar to your favorites'
  }
};

export default function CrossDomainRecommendations({ 
  userContext, 
  musicArtists, 
  topScoredArtists,
  userTags,
  spotifyToken,
  location = "Mumbai, India",  // Default location for Indian users
  locationRadius = 50000,  // Default 50km radius
  onClose 
}: CrossDomainRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<CrossDomainData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [selectedItem, setSelectedItem] = useState<RecommendationItem | null>(null);
  const [progressInterval, setProgressInterval] = useState<NodeJS.Timeout | null>(null);
  const [cacheStatus, setCacheStatus] = useState<'loading' | 'cached' | 'fresh' | 'error'>('loading');

  useEffect(() => {
    fetchCrossDomainRecommendations();
  }, []);

  useEffect(() => {
    return () => {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
    };
  }, [progressInterval]);

  // Handle keyboard events for popup and prevent body scroll
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && selectedItem) {
        setSelectedItem(null);
      }
    };

    if (selectedItem) {
      // Prevent body scroll when modal is open
      const originalStyle = window.getComputedStyle(document.body).overflow;
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.width = '100%';
      document.body.style.top = `-${window.scrollY}px`;
      
      document.addEventListener('keydown', handleKeyDown);
      
      return () => {
        document.body.style.overflow = originalStyle;
        document.body.style.position = '';
        document.body.style.width = '';
        document.body.style.top = '';
        window.scrollTo(0, parseInt(document.body.style.top || '0') * -1);
        document.removeEventListener('keydown', handleKeyDown);
      };
    } else {
      // Restore body scroll when modal is closed
      document.body.style.overflow = 'unset';
      document.body.style.position = '';
      document.body.style.width = '';
      document.body.style.top = '';
    }
  }, [selectedItem]);

  const clearServerCache = async () => {
    try {
      await fetch('http://localhost:5500/clear-cache', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      console.error('Failed to clear server cache:', error);
    }
  };

  const fetchCrossDomainRecommendations = async (forceRefresh = false) => {
    setLoading(true);
    setError(null);
    setProgress(0);
    setCacheStatus('loading');

    // Generate request hash for caching
    const requestHash = generateRequestHash(
      userContext,
      musicArtists,
      topScoredArtists || [],
      userTags || [],
      forceRefresh,
      location,
      locationRadius
    );

    // Check cache first (unless forcing refresh)
    if (!forceRefresh) {
      const cachedData = crossDomainCache.getCachedData<CrossDomainData>(CACHE_KEY, requestHash);
      if (cachedData) {
        // Mark data as from cache
        cachedData.from_cache = true;
        setRecommendations(cachedData);
        setCacheStatus('cached');
        setLoading(false);
        
        // Auto-select the first domain that has data
        const domains = ['movie', 'TV show', 'podcast', 'book', 'music artist'];
        for (const domain of domains) {
          if (cachedData.recommendations_by_domain[domain]?.length > 0) {
            setSelectedDomain(domain);
            break;
          }
        }
        return;
      }
    }

    // Clear cache if forcing refresh
    if (forceRefresh) {
      crossDomainCache.clearCache(CACHE_KEY);
      await clearServerCache();
    }

    // Start progress simulation
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 10;
      });
    }, 500);
    setProgressInterval(interval);

    try {
      const response = await fetch('http://localhost:5500/crossdomain-recommendations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          spotify_token: spotifyToken,
          user_context: userContext,
          music_artists: musicArtists,
          top_scored_artists: topScoredArtists || [],
          user_tags: userTags || [],
          cache_bust: forceRefresh,  // Add cache busting
          force_refresh: forceRefresh,  // Add force refresh
          location: location,  // Use dynamic location from props
          location_radius: locationRadius  // Use dynamic radius from props
        }),
      });

      if (!response.ok) {
        let errorMessage = 'Failed to fetch recommendations';
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch (jsonError) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      let data;
      try {
        data = await response.json();
      } catch (jsonError) {
        throw new Error('Invalid JSON response from server');
      }
      
      // Cache the fresh data
      crossDomainCache.setCachedData(CACHE_KEY, requestHash, data);
      
      setRecommendations(data);
      setCacheStatus('fresh');
      
      // Auto-select the first domain that has data
      const domains = ['movie', 'TV show', 'podcast', 'book', 'music artist'];
      for (const domain of domains) {
        if (data.recommendations_by_domain[domain]?.length > 0) {
          setSelectedDomain(domain);
          break;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setCacheStatus('error');
    } finally {
      setLoading(false);
      setProgress(100);
      if (progressInterval) {
        clearInterval(progressInterval);
        setProgressInterval(null);
      }
    }
  };

  const handleDomainClick = (domain: string) => {
    setSelectedDomain(domain);
    if (!recommendations) {
      fetchCrossDomainRecommendations();
    }
  };

  const getCacheStatusText = () => {
    switch (cacheStatus) {
      case 'cached':
        return '📦 From Cache';
      case 'fresh':
        return '🆕 Fresh Data';
      case 'loading':
        return '⏳ Loading...';
      case 'error':
        return '❌ Error';
      default:
        return '';
    }
  };

  const getCacheStatusColor = () => {
    switch (cacheStatus) {
      case 'cached':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'fresh':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'loading':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const renderRecommendationCard = (item: RecommendationItem, index: number) => (
    <Card 
      key={index} 
      className="border-2 border-black comic-shadow bg-white hover:shadow-lg transition-all duration-200 cursor-pointer"
      onClick={() => setSelectedItem(item)}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {(item.properties?.image?.url || item.image_url) && (
            <img 
              src={item.properties?.image?.url || item.image_url} 
              alt={item.name}
              className="w-16 h-16 rounded-lg border-2 border-black object-cover"
              onError={(e) => {
                console.log(`Image failed to load for ${item.name}:`, e);
                e.currentTarget.style.display = 'none';
              }}
              onLoad={(e) => {
                console.log(`Image loaded successfully for ${item.name}`);
              }}
            />
          )}
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-black text-sm truncate">{item.name}</h3>
            {(item.properties?.description || item.description) && (
              <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                {item.properties?.description || item.description}
              </p>
            )}
            
            {/* Enhanced metadata display */}
            <div className="space-y-1 mt-2">
              {(item.properties?.year || item.properties?.release_year || item.properties?.publication_year) && (
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {item.properties.year || item.properties.release_year || item.properties.publication_year}
                </p>
              )}
              {item.properties?.genre && (
                <p className="text-xs text-blue-600 font-medium">{item.properties.genre}</p>
              )}
              {(item.properties?.genres as string[]) && Array.isArray(item.properties.genres) && item.properties.genres.length > 0 && (
                <p className="text-xs text-purple-600 font-medium">{item.properties.genres.slice(0, 2).join(', ')}</p>
              )}
              {(item.properties?.runtime || item.properties?.duration) && (
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {item.properties.runtime || item.properties.duration}
                </p>
              )}
              {(item.properties?.episodes || item.properties?.episode_count) && (
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <Tv className="w-3 h-3" />
                  {(item.properties.episodes || item.properties.episode_count)} episodes
                </p>
              )}
              {item.properties?.page_count && (
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <BookOpen className="w-3 h-3" />
                  {item.properties.page_count} pages
                </p>
              )}
              {item.properties?.followers && (
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <User className="w-3 h-3" />
                  {item.properties.followers.toLocaleString()} followers
                </p>
              )}
              {item.properties?.content_rating && (
                <p className="text-xs text-orange-600 font-medium">{item.properties.content_rating}</p>
              )}
            </div>
            
            <div className="flex items-center gap-2 mt-2">
              {item.affinity_score && (
                <Badge variant="outline" className="text-xs">
                  <Star className="w-3 h-3 mr-1" />
                  {item.affinity_score}
                </Badge>
              )}
              {item.popularity && (
                <Badge variant="outline" className="text-xs">
                  <Award className="w-3 h-3 mr-1" />
                  {item.popularity}
                </Badge>
              )}
              {item.cultural_relevance && (
                <Badge variant="outline" className="text-xs">
                  <Globe className="w-3 h-3 mr-1" />
                  {item.cultural_relevance}
                </Badge>
              )}
            </div>
            
            {item.source_artist && (
              <p className="text-xs text-gray-500 mt-1">
                Based on: <span className="font-medium">{item.source_artist}</span>
              </p>
            )}
            
            {/* Quick tags preview */}
            {item.tags && item.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {item.tags.slice(0, 3).map((tag, tagIndex) => (
                  <span key={tagIndex} className="text-xs bg-gray-100 text-gray-600 px-1 py-0.5 rounded">
                    {tag}
                  </span>
                ))}
                {item.tags.length > 3 && (
                  <span className="text-xs text-gray-400">+{item.tags.length - 3} more</span>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderDetailedPopup = () => {
    if (!selectedItem) return null;

    const modalContent = (
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="detail-title"
        aria-describedby="detail-description"
        style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0,
          overflow: 'hidden',
          touchAction: 'none'
        }}
        onClick={(e) => {
          if (e.target === e.currentTarget) {
            setSelectedItem(null);
          }
        }}
        onTouchMove={(e) => e.preventDefault()}
      >
        <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border-4 border-black comic-shadow relative z-[10000]">
          <div className="p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <Button
                onClick={() => setSelectedItem(null)}
                variant="outline"
                className="border-2 border-black"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Discover
              </Button>
              <Button
                onClick={() => setSelectedItem(null)}
                variant="outline"
                className="border-2 border-black"
                aria-label="Close detailed view"
              >
                ✕
              </Button>
            </div>

            {/* Content */}
            <div className="space-y-4">
              {/* Image and Title */}
              <div className="flex items-start gap-4">
                {(selectedItem.properties?.image?.url || selectedItem.image_url) && (
                  <img 
                    src={selectedItem.properties?.image?.url || selectedItem.image_url} 
                    alt={selectedItem.name}
                    className="w-24 h-24 rounded-lg border-2 border-black object-cover"
                    onError={(e) => {
                      console.log(`Detailed popup image failed to load for ${selectedItem.name}:`, e);
                      e.currentTarget.style.display = 'none';
                    }}
                    onLoad={(e) => {
                      console.log(`Detailed popup image loaded successfully for ${selectedItem.name}`);
                    }}
                  />
                )}
                <div className="flex-1">
                  <h2 id="detail-title" className="text-2xl font-bold text-black mb-2">{selectedItem.name}</h2>
                  {selectedItem.properties?.description && (
                    <p id="detail-description" className="text-gray-600 mb-2">{selectedItem.properties.description}</p>
                  )}
                </div>
              </div>

              {/* Enhanced Metadata Sections */}
              <div className="space-y-6">
                {/* Key Details */}
                <div className="bg-gray-50 p-4 rounded-lg border-2 border-gray-200">
                  <h3 className="font-bold text-black mb-3 flex items-center gap-2">
                    <Database className="w-4 h-4" />
                    Key Details
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {(selectedItem.properties?.year || selectedItem.properties?.release_year || selectedItem.properties?.publication_year) && (
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-gray-500" />
                        <span className="text-sm">Year: {selectedItem.properties.year || selectedItem.properties.release_year || selectedItem.properties.publication_year}</span>
                      </div>
                    )}
                    {selectedItem.properties?.genre && (
                      <div className="flex items-center gap-2">
                        <Award className="w-4 h-4 text-gray-500" />
                        <span className="text-sm">Genre: {selectedItem.properties.genre}</span>
                      </div>
                    )}
                    {selectedItem.properties?.content_rating && (
                      <div className="flex items-center gap-2">
                        <Award className="w-4 h-4 text-gray-500" />
                        <span className="text-sm">Rating: {selectedItem.properties.content_rating}</span>
                      </div>
                    )}
                    {selectedItem.properties?.language && (
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4 text-gray-500" />
                        <span className="text-sm">Language: {selectedItem.properties.language}</span>
                      </div>
                    )}
                    {selectedItem.properties?.format && (
                      <div className="flex items-center gap-2">
                        <BookOpen className="w-4 h-4 text-gray-500" />
                        <span className="text-sm">Format: {selectedItem.properties.format}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Creator Information */}
                {(selectedItem.properties?.director || selectedItem.properties?.author || selectedItem.properties?.host || selectedItem.properties?.publisher || selectedItem.properties?.channel) && (
                  <div className="bg-blue-50 p-4 rounded-lg border-2 border-blue-200">
                    <h3 className="font-bold text-black mb-3 flex items-center gap-2">
                      <User className="w-4 h-4" />
                      Creator Information
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {selectedItem.properties?.director && (
                        <div className="flex items-center gap-2">
                          <Film className="w-4 h-4 text-blue-500" />
                          <span className="text-sm">Director: {selectedItem.properties.director}</span>
                        </div>
                      )}
                      {selectedItem.properties?.author && (
                        <div className="flex items-center gap-2">
                          <BookOpen className="w-4 h-4 text-blue-500" />
                          <span className="text-sm">Author: {selectedItem.properties.author}</span>
                        </div>
                      )}
                      {selectedItem.properties?.host && (
                        <div className="flex items-center gap-2">
                          <Headphones className="w-4 h-4 text-blue-500" />
                          <span className="text-sm">Host: {selectedItem.properties.host}</span>
                        </div>
                      )}
                      {selectedItem.properties?.channel && (
                        <div className="flex items-center gap-2">
                          <Headphones className="w-4 h-4 text-blue-500" />
                          <span className="text-sm">Channel: {selectedItem.properties.channel}</span>
                        </div>
                      )}
                      {selectedItem.properties?.publisher && (
                        <div className="flex items-center gap-2">
                          <BookOpen className="w-4 h-4 text-blue-500" />
                          <span className="text-sm">Publisher: {selectedItem.properties.publisher}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Movie-specific Information */}
                {selectedItem.properties?.production_companies && selectedItem.properties.production_companies.length > 0 && (
                  <div className="bg-red-50 p-4 rounded-lg border-2 border-red-200">
                    <h3 className="font-bold text-black mb-3 flex items-center gap-2">
                      <Film className="w-4 h-4" />
                      Movie Details
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-start gap-2">
                        <Film className="w-4 h-4 text-red-500 mt-0.5" />
                        <div>
                          <span className="text-sm font-medium">Production Companies:</span>
                          <div className="text-sm text-gray-600 mt-1">
                            {selectedItem.properties.production_companies.join(', ')}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* TV Show-specific Information */}
                {selectedItem.properties?.websites && selectedItem.properties.websites.length > 0 && (
                  <div className="bg-blue-50 p-4 rounded-lg border-2 border-blue-200">
                    <h3 className="font-bold text-black mb-3 flex items-center gap-2">
                      <Tv className="w-4 h-4" />
                      TV Show Details
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-start gap-2">
                        <ExternalLink className="w-4 h-4 text-blue-500 mt-0.5" />
                        <div>
                          <span className="text-sm font-medium">Official Websites:</span>
                          <div className="text-sm text-gray-600 mt-1">
                            {selectedItem.properties.websites.map((website, idx) => (
                              <div key={idx} className="mb-1">
                                <a 
                                  href={website} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:text-blue-800 underline"
                                >
                                  {website}
                                </a>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}



                {/* Media Details */}
                {(selectedItem.properties?.runtime || selectedItem.properties?.duration || selectedItem.properties?.episodes || selectedItem.properties?.episode_count || selectedItem.properties?.seasons || selectedItem.properties?.albums || selectedItem.properties?.page_count) && (
                  <div className="bg-green-50 p-4 rounded-lg border-2 border-green-200">
                    <h3 className="font-bold text-black mb-3 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Media Details
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {(selectedItem.properties?.runtime || selectedItem.properties?.duration) && (
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-green-500" />
                          <span className="text-sm">Runtime: {selectedItem.properties.runtime || selectedItem.properties.duration}</span>
                        </div>
                      )}
                      {(selectedItem.properties?.episodes || selectedItem.properties?.episode_count) && (
                        <div className="flex items-center gap-2">
                          <Tv className="w-4 h-4 text-green-500" />
                          <span className="text-sm">Episodes: {selectedItem.properties.episodes || selectedItem.properties.episode_count}</span>
                        </div>
                      )}
                      {selectedItem.properties?.seasons && (
                        <div className="flex items-center gap-2">
                          <Tv className="w-4 h-4 text-green-500" />
                          <span className="text-sm">Seasons: {selectedItem.properties.seasons}</span>
                        </div>
                      )}
                      {selectedItem.properties?.albums && (
                        <div className="flex items-center gap-2">
                          <Music className="w-4 h-4 text-green-500" />
                          <span className="text-sm">Albums: {selectedItem.properties.albums}</span>
                        </div>
                      )}
                      {selectedItem.properties?.page_count && (
                        <div className="flex items-center gap-2">
                          <BookOpen className="w-4 h-4 text-green-500" />
                          <span className="text-sm">Pages: {selectedItem.properties.page_count}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Artist/Music Specific */}
                {(selectedItem.properties?.followers || selectedItem.properties?.genres || selectedItem.properties?.spotify_url) && (
                  <div className="bg-orange-50 p-4 rounded-lg border-2 border-orange-200">
                    <h3 className="font-bold text-black mb-3 flex items-center gap-2">
                      <Music className="w-4 h-4" />
                      Artist Information
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {selectedItem.properties?.followers && (
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-orange-500" />
                          <span className="text-sm">Followers: {selectedItem.properties.followers.toLocaleString()}</span>
                        </div>
                      )}
                      {selectedItem.properties?.genres && Array.isArray(selectedItem.properties.genres) && selectedItem.properties.genres.length > 0 && (
                        <div className="flex items-center gap-2">
                          <Award className="w-4 h-4 text-orange-500" />
                          <span className="text-sm">Genres: {selectedItem.properties.genres.join(', ')}</span>
                        </div>
                      )}
                      {selectedItem.properties?.spotify_url && (
                        <div className="flex items-center gap-2">
                          <Music className="w-4 h-4 text-orange-500" />
                          <span className="text-sm">Spotify: Available</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Ratings & Reviews */}
                {selectedItem.properties?.rating && (
                  <div className="bg-purple-50 p-4 rounded-lg border-2 border-purple-200">
                    <h3 className="font-bold text-black mb-3 flex items-center gap-2">
                      <Star className="w-4 h-4" />
                      Ratings & Reviews
                    </h3>
                    <div className="flex items-center gap-2">
                      <Star className="w-4 h-4 text-purple-500" />
                      <span className="text-sm">Rating: {selectedItem.properties.rating}</span>
                    </div>
                  </div>
                )}



                {/* External URLs */}
                {(selectedItem.properties?.external_urls || selectedItem.properties?.url || selectedItem.properties?.spotify_url || selectedItem.external) && (
                  <div className="bg-indigo-50 p-4 rounded-lg border-2 border-indigo-200">
                    <h3 className="font-bold text-black mb-3 flex items-center gap-2">
                      <ExternalLink className="w-4 h-4" />
                      External Links
                    </h3>
                    <div className="space-y-2">
                      {selectedItem.properties?.external_urls && Object.entries(selectedItem.properties.external_urls).map(([platform, url]) => (
                        <div key={platform} className="flex items-center gap-2">
                          <ExternalLink className="w-4 h-4 text-indigo-500" />
                          <span className="text-sm capitalize">{platform}:</span>
                          <a 
                            href={url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:text-blue-800 underline"
                          >
                            Visit {platform}
                          </a>
                        </div>
                      ))}
                      {selectedItem.properties?.url && (
                        <div className="flex items-center gap-2">
                          <ExternalLink className="w-4 h-4 text-indigo-500" />
                          <span className="text-sm">Website:</span>
                          <a 
                            href={selectedItem.properties.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:text-blue-800 underline"
                          >
                            Visit Website
                          </a>
                        </div>
                      )}
                      {selectedItem.properties?.spotify_url && (
                        <div className="flex items-center gap-2">
                          <Music className="w-4 h-4 text-indigo-500" />
                          <span className="text-sm">Spotify:</span>
                          <a 
                            href={selectedItem.properties.spotify_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:text-blue-800 underline"
                          >
                            Open in Spotify
                          </a>
                        </div>
                      )}
                      {/* Qloo API External Links */}
                      {selectedItem.external && Object.entries(selectedItem.external).map(([platform, url]) => (
                        <div key={platform} className="flex items-center gap-2">
                          <ExternalLink className="w-4 h-4 text-indigo-500" />
                          <span className="text-sm capitalize">{platform}:</span>
                          <a 
                            href={url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:text-blue-800 underline"
                          >
                            Visit {platform}
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* User-Friendly Recommendation Info */}
              <div className="bg-blue-50 p-4 rounded-lg border-2 border-blue-200">
                <h3 className="font-bold text-black mb-3 flex items-center gap-2">
                  <Star className="w-4 h-4" />
                  Why This Was Recommended
                </h3>
                <div className="space-y-2">
                  {selectedItem.source_artist && (
                    <div className="flex items-center gap-2">
                      <Music className="w-4 h-4 text-blue-500" />
                      <span className="text-sm">
                        <span className="font-medium">Recommended because you like:</span> {selectedItem.source_artist}
                      </span>
                    </div>
                  )}
                  {selectedItem.selected_tag && (
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-blue-500" />
                      <span className="text-sm">
                        <span className="font-medium">Matches your interest in:</span> {selectedItem.selected_tag}
                      </span>
                    </div>
                  )}
                  {selectedItem.affinity_score && (
                    <div className="flex items-center gap-2">
                      <Star className="w-4 h-4 text-blue-500" />
                      <span className="text-sm">
                        <span className="font-medium">Match score:</span> {Math.round(selectedItem.affinity_score * 10)}/10
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* External Links */}
              {(selectedItem.properties?.url || selectedItem.properties?.spotify_url || selectedItem.url) && (
                <div className="flex gap-2">
                  {selectedItem.properties?.url && (
                    <Button asChild className="bg-blue-500 hover:bg-blue-600 text-white font-bold border-2 border-black comic-shadow transition-colors">
                      <a href={selectedItem.properties.url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Visit Website
                      </a>
                    </Button>
                  )}
                  {selectedItem.properties?.spotify_url && (
                    <Button asChild className="bg-green-500 hover:bg-green-600 text-white font-bold border-2 border-black comic-shadow transition-colors">
                      <a href={selectedItem.properties.spotify_url} target="_blank" rel="noopener noreferrer">
                        <Music className="w-4 h-4 mr-2" />
                        Open in Spotify
                      </a>
                    </Button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );

    // Use portal to render modal at the top level
    return createPortal(modalContent, document.body);
  };

  return (
    <div className="w-full max-w-6xl mx-auto py-4 px-4">
      {/* Header */}
      <div className="text-center mb-6">
        <ComicText
          fontSize={2.5}
          className="text-[1.5rem] sm:text-[2rem] md:text-[2.5rem] mb-2"
        >
          Discover More Based on Your Taste
        </ComicText>
        <p className="text-sm text-gray-600 font-comic">
          Explore movies, TV shows, podcasts, books, and more artists that match your vibe
        </p>
        
        {/* Helpful Note */}
        <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-3 mt-3 max-w-md mx-auto">
          <p className="text-xs text-blue-700 font-comic">
            💡 <strong>Getting the same recommendations?</strong> Click "Refresh (Clear Cache)" below to discover fresh content!
          </p>
        </div>
        
        {/* Cache Status and Controls */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-4">
          {/* Cache Status Indicator */}
          {cacheStatus !== 'loading' && (
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border-2 font-bold text-sm ${getCacheStatusColor()}`}>
              <Database className="w-4 h-4" />
              {getCacheStatusText()}
            </div>
          )}
          
          {/* Refresh Button */}
          <Button 
            onClick={() => fetchCrossDomainRecommendations(true)}
            className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg border-2 border-black comic-shadow flex items-center gap-2 transition-colors"
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Refreshing...' : 'Refresh (Clear Cache)'}
          </Button>
          
          {/* Clear Local Cache Only */}
          <Button 
            onClick={() => {
              crossDomainCache.clearCache(CACHE_KEY);
              setCacheStatus('loading');
              fetchCrossDomainRecommendations();
            }}
            variant="outline"
            className="border-2 border-black comic-shadow text-sm"
            disabled={loading}
          >
            Clear Local Cache
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-sm text-gray-600 font-comic">
            Discovering amazing content for you...
          </p>
          <Progress value={progress} className="w-full max-w-md mx-auto mt-4" />
          <p className="text-xs text-gray-500 mt-2">{Math.round(progress)}%</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="text-center py-8">
          <div className="bg-red-50 border-2 border-red-500 rounded-lg p-4 max-w-md mx-auto">
            <p className="text-red-700 font-bold text-sm">{error}</p>
            <div className="flex flex-col sm:flex-row gap-2 mt-3 justify-center">
              <Button 
                onClick={() => fetchCrossDomainRecommendations()}
                className="bg-red-500 hover:bg-red-600 text-white font-bold border-2 border-black comic-shadow transition-colors"
              >
                Try Again
              </Button>
              <Button 
                onClick={() => {
                  crossDomainCache.clearCache(CACHE_KEY);
                  setError(null);
                  fetchCrossDomainRecommendations();
                }}
                variant="outline"
                className="border-2 border-black"
              >
                Clear Cache & Retry
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations Display */}
      {recommendations && !loading && !error && (
        <div className="space-y-8">


          {/* Show all domains with data */}
          {Object.entries(domainConfig).map(([domain, config]) => {
            const domainRecommendations = recommendations.recommendations_by_domain[domain as keyof typeof recommendations.recommendations_by_domain];
            
            if (!domainRecommendations || domainRecommendations.length === 0) {
              return null;
            }

            const IconComponent = config.icon;
            
            return (
              <div key={domain} className="space-y-4">
                {/* Domain Header */}
                <div className="text-center">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <IconComponent className="w-6 h-6" />
                    <h2 className="text-xl font-bold text-black font-comic">
                      {config.title}
                    </h2>
                  </div>
                  <p className="text-sm text-gray-600 font-comic">
                    {config.description}
                  </p>
                </div>

                {/* Recommendations Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {domainRecommendations.map((item, index) => 
                    renderRecommendationCard(item, index)
                  )}
                </div>
              </div>
            );
          })}

          {/* No Recommendations Found */}
          {(() => {
            const hasAnyRecommendations = Object.entries(domainConfig).some(([domain, config]) => {
              const domainRecommendations = recommendations.recommendations_by_domain[domain as keyof typeof recommendations.recommendations_by_domain];
              return domainRecommendations && domainRecommendations.length > 0;
            });

            if (!hasAnyRecommendations) {
              return (
                <div className="text-center py-8">
                  <div className="bg-yellow-50 border-2 border-yellow-500 rounded-lg p-6 max-w-md mx-auto">
                    <p className="text-yellow-700 font-bold text-lg mb-2">No Recommendations Found</p>
                    <p className="text-yellow-600 text-sm mb-4">
                      We couldn't find any cross-domain recommendations for your current taste profile.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-2 justify-center">
                      <Button 
                        onClick={() => fetchCrossDomainRecommendations(true)}
                        className="bg-yellow-500 hover:bg-yellow-600 text-white"
                      >
                        Try Again with Fresh Data
                      </Button>
                      <Button 
                        onClick={() => {
                          crossDomainCache.clearCache(CACHE_KEY);
                          fetchCrossDomainRecommendations();
                        }}
                        variant="outline"
                        className="border-2 border-black"
                      >
                        Clear Cache & Retry
                      </Button>
                    </div>
                  </div>
                </div>
              );
            }
            return null;
          })()}


        </div>
      )}

      {/* Close Button */}
      {onClose && (
        <div className="text-center mt-6">
          <Button 
            onClick={onClose}
            variant="outline"
            className="border-2 border-black comic-shadow"
          >
            Close
          </Button>
        </div>
      )}

      {/* Detailed Popup */}
      {renderDetailedPopup()}
    </div>
  );
} 