import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Loader2, Sparkles, Music, Calendar, TrendingUp, Star, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { apiUrl } from '@/config/env';

interface NewArtist {
  artist_name: string;
  first_seen: string;
  genre: string;
  popularity_score: number;
  recommendation_count: number;
}

interface ArtistDetails {
  id: string;
  name: string;
  image: string | null;
  genres: string[];
  popularity: number;
  followers: number;
  spotify_url: string;
  uri: string;
}

interface NewArtistsIndicatorProps {
  userId: string;
  spotifyToken?: string;
  currentArtists?: string[];
  onArtistClick?: (artistName: string) => void;
}

const NewArtistsIndicator: React.FC<NewArtistsIndicatorProps> = ({
  userId,
  spotifyToken,
  currentArtists = [],
  onArtistClick
}) => {
  const [newArtists, setNewArtists] = useState<NewArtist[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const [artistDetails, setArtistDetails] = useState<Record<string, ArtistDetails>>({});
  const [loadingArtists, setLoadingArtists] = useState<Set<string>>(new Set());
  const [expandedGenres, setExpandedGenres] = useState<Set<string>>(new Set());

  const loadNewArtists = async () => {
    if (!userId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(apiUrl(`/recommendations/new-artists/${userId}?days=7`));
      if (!response.ok) {
        throw new Error('Failed to load new artists');
      }
      
      const data = await response.json();
      console.log('Raw new artists data:', data.new_artists);
      // Deduplicate artists by name to prevent duplicates
      const uniqueArtists = (data.new_artists || []).filter((artist: NewArtist, index: number, self: NewArtist[]) => 
        index === self.findIndex((a: NewArtist) => a.artist_name === artist.artist_name)
      );
      console.log('Deduplicated artists:', uniqueArtists);
      
      // Clear existing artist details when loading new data
      setArtistDetails({});
      setNewArtists(uniqueArtists);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load new artists');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNewArtists();
  }, [userId]);

  useEffect(() => {
    // Fetch artist details for all new artists using batch loading
    if (newArtists.length > 0 && spotifyToken) {
      const artistsToFetch = newArtists
        .map(artist => artist.artist_name)
        .filter(artistName => !artistDetails[artistName] && !loadingArtists.has(artistName));
      
      if (artistsToFetch.length > 0) {
        // Use batch loading for better performance
        fetchArtistDetailsBatch(artistsToFetch);
      }
    }
  }, [newArtists, spotifyToken]); // Removed artistDetails from dependency array

  const fetchArtistDetails = async (artistName: string) => {
    if (!spotifyToken || artistDetails[artistName] || loadingArtists.has(artistName)) {
      return;
    }

    console.log(`Fetching details for artist: ${artistName}`);
    setLoadingArtists(prev => new Set(prev).add(artistName));

    try {
      const response = await fetch(apiUrl('/artist-details'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          spotify_token: spotifyToken,
          artist_name: artistName
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log(`Artist details received for ${artistName}:`, data.artist);
        
        // Ensure we have valid image data
        const artistData = data.artist;
        if (artistData && artistData.images && artistData.images.length > 0) {
          // Use the highest quality image available
          const bestImage = artistData.images.reduce((best, current) => {
            return (current.width || 0) > (best.width || 0) ? current : best;
          });
          artistData.image = bestImage.url;
        } else {
          // Set a placeholder if no image is available
          artistData.image = null;
        }
        
        setArtistDetails(prev => ({
          ...prev,
          [artistName]: artistData
        }));
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.warn(`Failed to fetch details for ${artistName}: ${response.status}`, errorData);
        
        // Set placeholder data for failed requests
        setArtistDetails(prev => ({
          ...prev,
          [artistName]: {
            id: '',
            name: artistName,
            image: null,
            genres: [],
            popularity: 0,
            followers: 0,
            spotify_url: '',
            uri: ''
          }
        }));
      }
    } catch (err) {
      console.error(`Failed to fetch details for ${artistName}:`, err);
      
      // Set placeholder data for failed requests
      setArtistDetails(prev => ({
        ...prev,
        [artistName]: {
          id: '',
          name: artistName,
          image: null,
          genres: [],
          popularity: 0,
          followers: 0,
          spotify_url: '',
          uri: ''
        }
      }));
    } finally {
      setLoadingArtists(prev => {
        const newSet = new Set(prev);
        newSet.delete(artistName);
        return newSet;
      });
    }
  };

  // Batch fetch artist details for better performance
  const fetchArtistDetailsBatch = async (artistNames: string[]) => {
    if (!spotifyToken || artistNames.length === 0) return;

    console.log(`Batch fetching details for ${artistNames.length} artists:`, artistNames);
    
    // Add all artists to loading state
    setLoadingArtists(prev => new Set([...prev, ...artistNames]));

    try {
      // Use the new batch endpoint for better performance
      const response = await fetch('http://localhost:5500/artist-details-batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          spotify_token: spotifyToken,
          artist_names: artistNames
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log(`Batch artist details received:`, data.results);
        
        // Process all results at once
        const newDetails = { ...artistDetails };
        
        Object.entries(data.results).forEach(([artistName, result]) => {
          if (result && typeof result === 'object' && 'artist' in result && result.artist) {
            const artistData = result.artist as any;
            if (artistData.images && artistData.images.length > 0) {
              // Use the highest quality image available
              const bestImage = artistData.images.reduce((best: any, current: any) => {
                return (current.width || 0) > (best.width || 0) ? current : best;
              });
              artistData.image = bestImage.url;
            } else {
              // Set a placeholder if no image is available
              artistData.image = null;
            }
            newDetails[artistName] = artistData;
          } else {
            // Set placeholder data for failed requests
            newDetails[artistName] = {
              id: '',
              name: artistName,
              image: null,
              genres: [],
              popularity: 0,
              followers: 0,
              spotify_url: '',
              uri: ''
            };
          }
        });
        
        // Update state with all results at once
        setArtistDetails(newDetails);
      } else {
        console.error('Batch fetch failed:', response.status);
        // Fallback to individual requests if batch fails
        const promises = artistNames.map(async (artistName) => {
          try {
            const response = await fetch('http://localhost:5500/artist-details', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                spotify_token: spotifyToken,
                artist_name: artistName
              })
            });

            if (response.ok) {
              const data = await response.json();
              const artistData = data.artist;
              if (artistData && artistData.images && artistData.images.length > 0) {
                const bestImage = artistData.images.reduce((best, current) => {
                  return (current.width || 0) > (best.width || 0) ? current : best;
                });
                artistData.image = bestImage.url;
              } else {
                artistData.image = null;
              }
              return { artistName, artistData };
            } else {
              return {
                artistName,
                artistData: {
                  id: '',
                  name: artistName,
                  image: null,
                  genres: [],
                  popularity: 0,
                  followers: 0,
                  spotify_url: '',
                  uri: ''
                }
              };
            }
          } catch (err) {
            console.error(`Failed to fetch details for ${artistName}:`, err);
            return {
              artistName,
              artistData: {
                id: '',
                name: artistName,
                image: null,
                genres: [],
                popularity: 0,
                followers: 0,
                spotify_url: '',
                uri: ''
              }
            };
          }
        });

        const results = await Promise.all(promises);
        setArtistDetails(prev => {
          const newDetails = { ...prev };
          results.forEach(({ artistName, artistData }) => {
            newDetails[artistName] = artistData;
          });
          return newDetails;
        });
      }

    } catch (err) {
      console.error('Batch fetch failed:', err);
    } finally {
      // Remove all artists from loading state
      setLoadingArtists(prev => {
        const newSet = new Set(prev);
        artistNames.forEach(name => newSet.delete(name));
        return newSet;
      });
    }
  };

  const handleArtistClick = (artistName: string) => {
    const details = artistDetails[artistName];
    if (details?.spotify_url) {
      window.open(details.spotify_url, '_blank');
    } else if (onArtistClick) {
      onArtistClick(artistName);
    }
  };

  const toggleGenreExpansion = (artistName: string) => {
    setExpandedGenres(prev => {
      const newSet = new Set(prev);
      if (newSet.has(artistName)) {
        newSet.delete(artistName);
      } else {
        newSet.add(artistName);
      }
      return newSet;
    });
  };

  const getPopularityColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100 border-green-200';
    if (score >= 60) return 'text-blue-600 bg-blue-100 border-blue-200';
    if (score >= 40) return 'text-yellow-600 bg-yellow-100 border-yellow-200';
    return 'text-gray-600 bg-gray-100 border-gray-200';
  };

  const getGenreColor = (genre: string) => {
    const genreColors: { [key: string]: string } = {
      'pop': 'bg-pink-100 text-pink-800 border-pink-200',
      'rock': 'bg-red-100 text-red-800 border-red-200',
      'hip-hop': 'bg-purple-100 text-purple-800 border-purple-200',
      'electronic': 'bg-blue-100 text-blue-800 border-blue-200',
      'jazz': 'bg-indigo-100 text-indigo-800 border-indigo-200',
      'classical': 'bg-gray-100 text-gray-800 border-gray-200',
      'country': 'bg-orange-100 text-orange-800 border-orange-200',
      'r&b': 'bg-purple-100 text-purple-800 border-purple-200',
      'indie': 'bg-green-100 text-green-800 border-green-200',
      'latin': 'bg-yellow-100 text-yellow-800 border-yellow-200',
    };
    
    return genreColors[genre.toLowerCase()] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            New Discoveries
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Finding new artists...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            New Discoveries
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center p-4">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={loadNewArtists} variant="outline">
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (newArtists.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            New Discoveries
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center p-8 text-gray-500">
            <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No new artists discovered yet</p>
            <p className="text-sm">Start exploring to discover new music!</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const displayedArtists = showAll ? newArtists : newArtists.slice(0, 5);

  return (
    <div className="w-full">
      {/* Header Section */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="flex items-center gap-2 text-xl font-bold text-gray-900 text-visible">
              <Sparkles className="h-5 w-5 text-yellow-500 flex-shrink-0" />
              <span className="break-words">New Discoveries</span>
            </h2>
            <p className="text-gray-600 mt-1 text-sm text-visible">
              Recently discovered artists you might love
            </p>
          </div>
          <div className="text-right flex-shrink-0 ml-4">
            <div className="text-2xl font-bold text-gray-900 text-visible">{newArtists.length}</div>
          </div>
        </div>
      </div>
      
      {/* Artist Cards Container */}
      <ScrollArea className="h-[600px] pr-4">
        <div className="space-y-4 pb-4">
          {displayedArtists.map((artist, index) => {
            const details = artistDetails[artist.artist_name];
            const isLoading = loadingArtists.has(artist.artist_name);
            
            return (
              <div key={`${artist.artist_name}-${index}`} className="discovery-card flex items-start gap-4">
                {/* Artist Image */}
                <div className="flex-shrink-0">
                  {details?.image ? (
                    <img
                      src={details.image}
                      alt={artist.artist_name}
                      className="w-16 h-16 rounded-full object-cover border-2 border-gray-300 shadow-sm"
                      onError={(e) => {
                        console.log(`Image failed to load for ${artist.artist_name}:`, e);
                        e.currentTarget.style.display = 'none';
                        // Show placeholder instead
                        const placeholder = e.currentTarget.nextElementSibling;
                        if (placeholder) {
                          placeholder.classList.remove('hidden');
                        }
                      }}
                      onLoad={(e) => {
                        console.log(`Image loaded successfully for ${artist.artist_name}`);
                      }}
                    />
                  ) : null}
                  {(!details?.image || isLoading) && (
                    <div className={`w-16 h-16 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center border-2 border-gray-300 ${details?.image ? 'hidden' : ''}`}>
                      {isLoading ? (
                        <Loader2 className="h-7 w-7 animate-spin text-white" />
                      ) : (
                        <span className="text-white font-bold text-xl">
                          {artist.artist_name.charAt(0).toUpperCase()}
                        </span>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Artist Info */}
                <div className="flex-1 min-w-0 flex flex-col gap-3">
                  <div className="flex-1 min-w-0">
                    {/* Artist Name */}
                    <div className="mb-3">
                      <h3 className="artist-name text-visible">
                        {artist.artist_name}
                      </h3>
                    </div>
                    
                    {/* Spotify Metadata */}
                    {details && (
                      <div className="space-y-3">
                        {/* Followers */}
                        <div className="text-sm text-gray-600 font-medium text-visible">
                          {details.followers.toLocaleString()} followers
                        </div>
                        
                                                {/* Genres */}
                        {details.genres && details.genres.length > 0 && (
                          <div className="space-y-2">
                            <div className="genre-container">
                              {details.genres.slice(0, 3).map((genre, idx) => (
                                <Badge 
                                  key={idx} 
                                  variant="secondary" 
                                  className="bg-yellow-100 border border-black text-black text-xs font-bold font-comic"
                                >
                                  {genre}
                                </Badge>
                              ))}
                                                             {details.genres.length > 3 && !expandedGenres.has(artist.artist_name) && (
                                 <Badge 
                                   variant="secondary" 
                                   className="bg-white border border-black text-black text-xs font-bold font-comic cursor-pointer hover:bg-gray-50 transition-colors"
                                   onClick={() => toggleGenreExpansion(artist.artist_name)}
                                 >
                                   +{details.genres.length - 3} more
                                   <ChevronDown className="h-3 w-3 ml-1" />
                                 </Badge>
                               )}
                            </div>
                            
                            {/* Expanded genres */}
                            {expandedGenres.has(artist.artist_name) && details.genres.length > 3 && (
                              <div className="genre-container">
                                {details.genres.slice(3).map((genre, idx) => (
                                  <Badge 
                                    key={idx + 3} 
                                    variant="secondary" 
                                    className="bg-yellow-100 border border-black text-black text-xs font-bold font-comic"
                                  >
                                    {genre}
                                  </Badge>
                                ))}
                                <Badge 
                                  variant="secondary" 
                                  className="bg-white border border-black text-black text-xs font-bold font-comic cursor-pointer hover:bg-gray-50 transition-colors"
                                  onClick={() => toggleGenreExpansion(artist.artist_name)}
                                >
                                  Show less
                                  <ChevronUp className="h-3 w-3 ml-1" />
                                </Badge>
                              </div>
                            )}
                          </div>
                        )}
                        
                                                 {/* Popularity Score */}
                         <div className="flex items-center gap-2">
                           <div className="popularity-bar">
                             <div 
                               className="popularity-fill"
                               style={{ width: `${details.popularity}%` }}
                             ></div>
                           </div>
                           <span className="text-sm text-gray-600 font-medium text-visible">{details.popularity}/100</span>
                         </div>
                      </div>
                    )}
                    
                                         {/* Loading State */}
                     {isLoading && (
                       <div className="space-y-2">
                         <div className="text-sm text-gray-400 flex items-center gap-2">
                           <Loader2 className="h-3 w-3 animate-spin" />
                           Loading metadata...
                         </div>
                         <div className="space-y-1">
                           <div className="h-2 bg-gray-200 rounded animate-pulse"></div>
                           <div className="h-2 bg-gray-200 rounded animate-pulse w-3/4"></div>
                         </div>
                       </div>
                     )}
                  </div>
                  
                  {/* Explore Artist Button */}
                  <div className="flex-shrink-0">
                    <button
                      onClick={() => handleArtistClick(artist.artist_name)}
                      className="explore-button flex items-center justify-center gap-2 text-sm px-4 py-2"
                    >
                      <Music className="h-4 w-4" />
                      <span>Explore Artist</span>
                      {details?.spotify_url && (
                        <ExternalLink className="h-3 w-3" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </ScrollArea>
      
      {/* Show More/Less Button */}
      {newArtists.length > 5 && (
        <div className="mt-6 text-center">
          <Button
            onClick={() => setShowAll(!showAll)}
            variant="outline"
            size="sm"
            className="border-2 border-black comic-shadow hover:bg-gray-50 transition-colors px-6 py-2"
          >
            {showAll ? 'Show Less' : `Show All ${newArtists.length} Artists`}
          </Button>
        </div>
      )}
    </div>
  );
};

export default NewArtistsIndicator; 