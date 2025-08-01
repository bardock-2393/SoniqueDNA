// Spotify Authentication Handler - External JS file to avoid CSP violations
const SPOTIFY_CONFIG = {
  clientId: '5b5e4ceb834347e6a6c3b998cfaf0088',
  redirectUri: 'http://15.207.204.90:8080/callback',
  scope: 'user-read-private user-read-email user-top-read user-read-recently-played playlist-modify-public playlist-modify-private user-read-playback-state user-read-currently-playing'
};

// Generate Spotify authorization URL
function generateSpotifyAuthUrl(forceReauth = false) {
  const state = generateState();
  const params = new URLSearchParams({
    client_id: SPOTIFY_CONFIG.clientId,
    response_type: 'code',
    redirect_uri: SPOTIFY_CONFIG.redirectUri,
    scope: SPOTIFY_CONFIG.scope,
    state: state
  });
  
  if (forceReauth) {
    params.append('show_dialog', 'true');
  }
  
  return `https://accounts.spotify.com/authorize?${params.toString()}`;
}

// Generate secure state parameter
function generateState() {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

// Redirect to Spotify authorization
function redirectToSpotify(forceReauth = false) {
  const authUrl = generateSpotifyAuthUrl(forceReauth);
  window.location.href = authUrl;
}

// Handle Spotify callback
function handleSpotifyCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');
  const error = params.get('error');
  
  if (error) {
    console.error('Spotify authorization error:', error);
    return { success: false, error };
  }
  
  if (code) {
    // Exchange code for access token
    return exchangeCodeForToken(code, state);
  }
  
  return { success: false, error: 'No authorization code received' };
}

// Exchange authorization code for access token
async function exchangeCodeForToken(code, state) {
  try {
    const response = await fetch('http://15.207.204.90:5500/exchange-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        code,
        redirect_uri: SPOTIFY_CONFIG.redirectUri,
        state
      })
    });
    
    const data = await response.json();
    
    if (data.access_token) {
      // Store tokens
      localStorage.setItem('spotify_token', data.access_token);
      if (data.refresh_token) {
        localStorage.setItem('spotify_refresh_token', data.refresh_token);
      }
      
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
      
      return { success: true, token: data.access_token };
    } else {
      return { success: false, error: data.error || 'Failed to exchange code for token' };
    }
  } catch (error) {
    console.error('Error exchanging code for token:', error);
    return { success: false, error: error.message };
  }
}

// Export functions for use in React components
window.SpotifyAuth = {
  redirectToSpotify,
  handleSpotifyCallback,
  generateSpotifyAuthUrl
}; 