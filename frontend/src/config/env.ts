// Environment configuration for the frontend
export const config = {
  // Spotify Configuration
  spotify: {
    clientId: import.meta.env.VITE_SPOTIFY_CLIENT_ID || 'f4b7a6f6cde94656ad7f0e8f0bfa8330',
    redirectUri: import.meta.env.VITE_SPOTIFY_REDIRECT_URI || 'https://soniquedna.deepsantoshwar.xyz/callback',
  },
  
  // Backend Configuration - Development mode uses EC2 IP
  backend: {
    url: import.meta.env.VITE_BACKEND_URL || (import.meta.env.DEV ? 'http://15.207.204.90:5500' : 'https://soniquedna.deepsantoshwar.xyz'),
  },
  
  // App Configuration
  app: {
    env: import.meta.env.VITE_APP_ENV || 'development',
  },
} as const;

// Type-safe environment variable access
export const getSpotifyClientId = () => config.spotify.clientId;
export const getSpotifyRedirectUri = () => config.spotify.redirectUri;
export const getBackendUrl = () => config.backend.url;

// API helper functions
export const apiUrl = (endpoint: string) => {
  const baseUrl = getBackendUrl();
  return `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
};

export const spotifyApiUrl = (endpoint: string) => {
  return apiUrl(endpoint);
}; 