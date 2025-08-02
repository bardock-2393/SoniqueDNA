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
  RefreshCw,
  X
} from 'lucide-react';
import { ComicText } from './magicui/comic-text';
import { crossDomainCache, cacheUtils } from '../utils/cacheManager';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';

interface CrossDomainRecommendationsProps {
  userContext: string;
  musicArtists: string[];
  topScoredArtists?: string[];
  userTags?: string[];
  spotifyToken: string;
  location?: string;
  locationRadius?: number;
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
  relevance_score?: number;
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
    finale_year?: number;
    
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
    
    // Legacy fields
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
    timestamp: forceRefresh ? Date.now() : Math.floor(Date.now() / 300000) * 300000
  };
  
  return btoa(JSON.stringify(data));
};

const domainConfig = {
  movie: {
    title: 'Movies',
    icon: Film,
    color: 'bg-red-500',
    hoverColor: 'hover:bg-red-600',
    description: 'Discover films that match your vibe',
    emoji: '🎬'
  },
  'TV show': {
    title: 'TV Shows',
    icon: Tv,
    color: 'bg-blue-500',
    hoverColor: 'hover:bg-blue-600',
    description: 'Series that complement your taste',
    emoji: '📺'
  },
  podcast: {
    title: 'Podcasts',
    icon: Headphones,
    color: 'bg-purple-500',
    hoverColor: 'hover:bg-purple-600',
    description: 'Audio content that resonates with you',
    emoji: '🎧'
  },
  book: {
    title: 'Books',
    icon: BookOpen,
    color: 'bg-green-500',
    hoverColor: 'hover:bg-green-600',
    description: 'Stories that align with your interests',
    emoji: '📚'
  },
  'music artist': {
    title: 'Music Artists',
    icon: Music,
    color: 'bg-orange-500',
    hoverColor: 'hover:bg-orange-600',
    description: 'Artists similar to your favorites',
    emoji: '🎵'
  }
};

export default function CrossDomainRecommendations({ 
  userContext, 
  musicArtists, 
  topScoredArtists,
  userTags,
  spotifyToken,
  location = "Mumbai, India",
  locationRadius = 50000,
  onClose 
}: CrossDomainRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<CrossDomainData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [selectedItem, setSelectedItem] = useState<RecommendationItem | null>(null);
  const [progressInterval, setProgressInterval] = useState<NodeJS.Timeout | null>(null);
  const [cacheStatus, setCacheStatus] = useState<'loading' | 'cached' | 'fresh' | 'error'>('loading');
  const [detailsOpen, setDetailsOpen] = useState(false);

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

  // Handle keyboard events for modal
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && detailsOpen) {
        setDetailsOpen(false);
        setSelectedItem(null);
      }
    };

    if (detailsOpen) {
      document.body.style.overflow = 'hidden';
      document.addEventListener('keydown', handleKeyDown);
      
      return () => {
        document.body.style.overflow = '';
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [detailsOpen]);

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

    const requestHash = generateRequestHash(
      userContext,
      musicArtists,
      topScoredArtists || [],
      userTags || [],
      forceRefresh,
      location,
      locationRadius
    );

    if (!forceRefresh) {
      const cachedData = crossDomainCache.getCachedData<CrossDomainData>(CACHE_KEY, requestHash);
      if (cachedData) {
        cachedData.from_cache = true;
        setRecommendations(cachedData);
        setCacheStatus('cached');
        setLoading(false);
        return;
      }
    }

    if (forceRefresh) {
      crossDomainCache.clearCache(CACHE_KEY);
      await clearServerCache();
    }

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
          cache_bust: forceRefresh,
          force_refresh: forceRefresh,
          location: location,
          location_radius: locationRadius
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
      
      crossDomainCache.setCachedData(CACHE_KEY, requestHash, data);
      
      setRecommendations(data);
      setCacheStatus('fresh');
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

  const handleItemClick = (item: RecommendationItem) => {
    setSelectedItem(item);
    setDetailsOpen(true);
  };

  const renderRecommendationCard = (item: RecommendationItem, domain: string, index: number) => {
    const config = domainConfig[domain as keyof typeof domainConfig];
    
    return (
      <div 
        key={index}
        className="comic-recommendation-card overflow-hidden cursor-pointer group relative flex-shrink-0 w-56 sm:w-60 lg:w-64"
        onClick={() => handleItemClick(item)}
      >
        <div className="relative h-full">
                     {/* Image Section */}
           <div className="relative h-36 sm:h-40 lg:h-44 bg-gradient-to-br from-yellow-200 via-orange-200 to-red-200 border-b-4 border-black overflow-hidden">
             {(item.properties?.image?.url || item.image_url) ? (
               <img
                 src={item.properties?.image?.url || item.image_url}
                 alt={item.name}
                 className="w-full h-full object-contain bg-white"
                                   onError={(e) => {
                    e.currentTarget.src = '/cat/404caty.jpg';
                  }}
               />
             ) : (
               <div className="w-full h-full flex items-center justify-center">
                 <span className="text-4xl sm:text-5xl">
                   {config?.emoji || '🎭'}
                 </span>
               </div>
             )}

            {/* Relevance score badge */}
            {item.relevance_score !== undefined && item.relevance_score > 0 && (
              <div className="absolute top-2 left-2 bg-blue-400 border-2 border-black rounded-full px-2 py-1 text-xs font-comic font-black comic-shadow">
                ⭐ {item.relevance_score.toFixed(1)}
              </div>
            )}

            {(item.properties?.release_year || item.properties?.publication_year) && (
              <div className="absolute top-2 right-2 bg-blue-400 border-2 border-black rounded-full px-2 py-1 text-xs font-comic font-black text-white comic-shadow">
                {item.properties.release_year || item.properties.publication_year}
              </div>
            )}

            <div className="absolute inset-0 bg-yellow-400 opacity-0 group-hover:opacity-20 transition-opacity duration-300 flex items-center justify-center">
              <span className="text-4xl sm:text-5xl animate-pulse">⭐</span>
            </div>
          </div>

          {/* Content Section */}
          <div className="p-3 sm:p-4 h-28 sm:h-32 lg:h-36 flex flex-col justify-between">
            <div className="font-comic font-black text-black text-sm sm:text-base leading-tight mb-2 line-clamp-2">
              {item.name}
            </div>

            <div className="flex-1 flex flex-col justify-center gap-2">
              {item.selected_tag && (
                <div className="bg-purple-300 border-2 border-black rounded-lg px-2 py-1 text-xs font-comic font-black text-center comic-shadow">
                  #{item.selected_tag}
                </div>
              )}

              {item.source_artist && (
                <div className="text-xs text-gray-700 flex items-center justify-center gap-1 font-comic font-bold">
                  <span>🎵</span>
                  <span className="truncate">From: {item.source_artist}</span>
                </div>
              )}

                             {/* Domain-specific info */}
               <div className="text-xs text-gray-700 flex items-center justify-center gap-1 font-comic font-bold">
                 {domain === 'movie' && item.properties?.duration && (
                   <>
                     <span>⏰</span>
                     <span>{(() => {
                       const duration = typeof item.properties.duration === 'string' ? parseInt(item.properties.duration) : item.properties.duration;
                       if (isNaN(duration)) return item.properties.duration;
                       return `${Math.floor(duration / 60)}h ${duration % 60}m`;
                     })()}</span>
                   </>
                 )}
                {domain === 'book' && item.properties?.page_count && (
                  <>
                    <span>📖</span>
                    <span>{item.properties.page_count} pages</span>
                  </>
                )}
                {domain === 'TV show' && (item.properties?.release_year && item.properties?.finale_year) && (
                  <>
                    <span>📅</span>
                    <span>{item.properties.release_year} - {item.properties.finale_year}</span>
                  </>
                )}
                {domain === 'podcast' && item.properties?.episode_count && (
                  <>
                    <span>🎙️</span>
                    <span>{item.properties.episode_count} eps</span>
                  </>
                )}
              </div>
            </div>

            {/* Bottom action */}
            <div className="mt-2 text-center">
              <div className="bg-yellow-300 border-2 border-black rounded-full px-3 py-1 text-xs font-comic font-black comic-shadow group-hover:bg-yellow-400 transition-colors">
                CLICK TO EXPLORE!
              </div>
            </div>
          </div>

          {/* Hover effect */}
          <div className="absolute -top-2 -left-2 bg-white border-3 border-black rounded-full w-8 h-8 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 comic-shadow transform group-hover:scale-110">
            <span className="text-lg">💥</span>
          </div>
        </div>
      </div>
    );
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
            className="comic-button bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg border-2 border-black comic-shadow flex items-center gap-2 transition-colors"
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
            className="comic-button border-2 border-black comic-shadow text-sm"
            disabled={loading}
          >
            Clear Local Cache
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="comic-recommendation-card mb-6">
            <div className="flex items-center gap-4 mb-4">
              <img src="/cat/404caty.jpg" alt="Loading Cat" className="w-12 h-12 rounded-full comic-border animate-pulse" />
              <div>
                <span className="font-bold text-black font-comic text-lg">Caty is thinking...</span>
                <div className="text-gray-600 text-sm font-comic mt-1">
                  😼 "Hold on, human! I'm analyzing your music taste to find movies, books, and shows you'll love..."
                </div>
              </div>
              <div className="text-right">
                <span className="font-bold text-black font-comic text-lg">
                  {progress > 100 ? '102.475135245687%' : `${progress}%`}
                </span>
                {progress > 100 && (
                  <div className="text-xs text-red-500 font-comic">(Caty's math skills! 😸)</div>
                )}
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="mb-4">
              <div className="w-full bg-gray-200 rounded-full h-3 sm:h-4 border-2 border-black comic-shadow overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-yellow-400 via-orange-400 to-red-400 transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
            
            <p className="text-sm text-gray-600 font-comic">
              Discovering amazing content for you...
            </p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="text-center py-8">
          <div className="comic-recommendation-card bg-red-50 border-2 border-red-500 rounded-lg p-4 max-w-md mx-auto">
            <p className="text-red-700 font-bold text-sm">{error}</p>
            <div className="flex flex-col sm:flex-row gap-2 mt-3 justify-center">
              <Button 
                onClick={() => fetchCrossDomainRecommendations()}
                className="comic-button bg-red-500 hover:bg-red-600 text-white font-bold border-2 border-black comic-shadow transition-colors"
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
                className="comic-button border-2 border-black"
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
                  <div className="comic-section-header max-w-2xl mx-auto">
                    <div className="flex items-center justify-center gap-3 sm:gap-4">
                      <img src="/cat/404caty.jpg" alt={`Cat ${domain}`} className="w-10 h-10 sm:w-12 sm:h-12 rounded-full comic-border comic-shadow" />
                      <div className="text-center">
                        <ComicText fontSize={1.8} className="uppercase tracking-wider text-sm sm:text-base">
                          {config.title}
                        </ComicText>
                        <div className="font-comic font-bold text-sm sm:text-base lg:text-lg text-black mt-1">
                          😼 Caty's Picks!
                        </div>
                      </div>
                      <div className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 bg-white comic-border rounded-full w-6 h-6 sm:w-8 sm:h-8 flex items-center justify-center font-comic font-black text-sm sm:text-lg comic-shadow">
                        {domainRecommendations.length}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recommendations Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {domainRecommendations.map((item, index) => 
                    renderRecommendationCard(item, domain, index)
                  )}
                </div>

                {/* Section Divider */}
                <div className="mt-6 sm:mt-8 lg:mt-12 flex items-center justify-center">
                  <div className="bg-gradient-to-r from-transparent via-black to-transparent h-1 sm:h-2 w-full max-w-md comic-shadow"></div>
                  <div className="mx-3 sm:mx-4 bg-yellow-400 comic-border rounded-full w-8 h-8 sm:w-10 sm:h-10 flex items-center justify-center font-comic font-black comic-shadow-lg comic-pulse">
                    ⭐
                  </div>
                  <div className="bg-gradient-to-r from-black via-transparent to-transparent h-1 sm:h-2 w-full max-w-md comic-shadow"></div>
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
                  <div className="comic-recommendation-card bg-yellow-50 border-2 border-yellow-500 rounded-lg p-6 max-w-md mx-auto">
                    <p className="text-yellow-700 font-bold text-lg mb-2">No Recommendations Found</p>
                    <p className="text-yellow-600 text-sm mb-4">
                      We couldn't find any cross-domain recommendations for your current taste profile.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-2 justify-center">
                      <Button 
                        onClick={() => fetchCrossDomainRecommendations(true)}
                        className="comic-button bg-yellow-500 hover:bg-yellow-600 text-white"
                      >
                        Try Again with Fresh Data
                      </Button>
                      <Button 
                        onClick={() => {
                          crossDomainCache.clearCache(CACHE_KEY);
                          fetchCrossDomainRecommendations();
                        }}
                        variant="outline"
                        className="comic-button border-2 border-black"
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
            className="comic-button border-2 border-black comic-shadow"
          >
            Close
          </Button>
        </div>
      )}

      {/* Details Modal */}
      <Dialog open={detailsOpen} onOpenChange={setDetailsOpen}>
        <DialogContent 
          className="bg-white border-4 border-black comic-shadow max-w-2xl mx-auto p-0 max-h-[90vh] flex flex-col"
          aria-describedby="details-description"
        >
          {selectedItem && (
            <>
              {/* Fixed Header */}
              <div className="p-4 sm:p-6 border-b-2 border-black bg-yellow-50">
                <p id="details-description" className="sr-only">
                  Detailed information about {selectedItem.name}
                </p>
                                 <div className="flex items-center gap-4">
                   {(selectedItem.properties?.image?.url || selectedItem.image_url) ? (
                     <img
                       src={selectedItem.properties?.image?.url || selectedItem.image_url}
                       alt={selectedItem.name}
                       className="w-16 h-16 sm:w-20 sm:h-20 rounded-lg border-2 border-black object-cover flex-shrink-0"
                                               onError={e => { 
                          e.currentTarget.src = '/cat/404caty.jpg'; 
                        }}
                     />
                   ) : (
                     <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-yellow-200 to-orange-300 rounded-lg border-2 border-black flex items-center justify-center flex-shrink-0">
                       <span className="text-2xl sm:text-3xl">🎭</span>
                     </div>
                   )}
                  <div className="flex-1 min-w-0">
                    <ComicText fontSize={1.3} className="mb-2 line-clamp-2">{selectedItem.name}</ComicText>
                    <div className="flex flex-wrap gap-2">
                      {(selectedItem.properties?.release_year || selectedItem.properties?.publication_year) && (
                        <div className="text-xs bg-gray-100 border border-black rounded px-2 py-1 font-bold font-comic">
                          {selectedItem.properties.release_year || selectedItem.properties.publication_year}
                        </div>
                      )}
                      {selectedItem.relevance_score !== undefined && selectedItem.relevance_score > 0 && (
                        <div className="text-xs bg-blue-100 border border-black rounded px-2 py-1 font-bold font-comic">
                          ⭐ {selectedItem.relevance_score.toFixed(1)} relevance
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
                {/* Selected Tag and Source Artist */}
                <div className="flex flex-wrap gap-2">
                  {selectedItem.selected_tag && (
                    <Badge className="text-xs bg-blue-100 text-blue-800 border border-blue-300 font-comic">
                      #{selectedItem.selected_tag}
                    </Badge>
                  )}
                  {selectedItem.source_artist && (
                    <div className="text-xs text-gray-500 flex items-center gap-1 font-comic bg-gray-50 border border-gray-300 rounded px-2 py-1">
                      <span>🎵</span>
                      <span>Based on: {selectedItem.source_artist}</span>
                    </div>
                  )}
                </div>

                {/* Description */}
                {(selectedItem.properties?.description || selectedItem.properties?.short_description || selectedItem.description) && (
                  <div className="bg-gray-50 border-2 border-gray-200 rounded-lg p-3">
                    <h4 className="font-comic font-bold text-sm mb-2 text-black">Description</h4>
                    <div
                      className="text-sm text-gray-700 font-comic leading-relaxed"
                      dangerouslySetInnerHTML={{
                        __html: (selectedItem.properties?.description || selectedItem.properties?.short_description || selectedItem.description || '').replace(/\n/g, '<br />')
                      }}
                    />
                  </div>
                )}

                {/* Tags */}
                {selectedItem.tags && selectedItem.tags.length > 0 && (
                  <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-3">
                    <h4 className="font-comic font-bold text-sm mb-2 text-black">Tags</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedItem.tags.slice(0, 8).map((tag: any, index: number) => (
                        <Badge key={index} className="bg-yellow-100 border border-black text-black text-xs font-bold font-comic">
                          {typeof tag === 'string' ? tag : tag.name || tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* External Links */}
                {(selectedItem.properties?.url || selectedItem.properties?.spotify_url || selectedItem.url) && (
                  <div className="bg-indigo-50 border-2 border-indigo-200 rounded-lg p-3">
                    <h4 className="font-comic font-bold text-sm mb-2 text-black">External Links</h4>
                    <div className="flex flex-wrap gap-2">
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
                  </div>
                )}
              </div>

              {/* Fixed Footer */}
              <div className="border-t-2 border-black p-4 bg-gray-50">
                <div className="flex justify-center">
                  <Button
                    onClick={() => setDetailsOpen(false)}
                    className="comic-button bg-yellow-200 hover:bg-yellow-300 text-black font-bold border-2 border-black font-comic comic-shadow"
                  >
                    Close
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
} 