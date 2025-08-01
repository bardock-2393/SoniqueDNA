// TypeScript declarations for Spotify authentication
declare global {
  interface Window {
    SpotifyAuth?: {
      redirectToSpotify: (forceReauth?: boolean) => void;
      handleSpotifyCallback: () => Promise<{ success: boolean; token?: string; error?: string }> | { success: boolean; token?: string; error?: string };
      generateSpotifyAuthUrl: (forceReauth?: boolean) => string;
    };
  }
}

export {}; 