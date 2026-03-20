/**
 * BoTTube Mobile App - API Service
 * Bounty #44: 100 RTC
 */

const API_BASE = 'https://bottube.ai/api';

// Get trending videos
export async function getTrendingVideos(limit = 20) {
  const response = await fetch(`${API_BASE}/videos?trending=1&limit=${limit}`);
  return response.json();
}

// Get video details
export async function getVideo(id) {
  const response = await fetch(`${API_BASE}/videos/${id}`);
  return response.json();
}

// Like a video
export async function likeVideo(id, token) {
  const response = await fetch(`${API_BASE}/videos/${id}/like`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
}

// Comment on a video
export async function commentOnVideo(id, text, token) {
  const response = await fetch(`${API_BASE}/videos/${id}/comments`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ text }),
  });
  return response.json();
}

// Subscribe to a channel
export async function subscribeToChannel(agentId, token) {
  const response = await fetch(`${API_BASE}/agents/${agentId}/subscribe`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
}

// Authenticate user
export async function login(email, password) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return response.json();
}

// Get user profile
export async function getProfile(token) {
  const response = await fetch(`${API_BASE}/users/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
}
