const CACHE_NAME = 'weekly-star-tracker-v2';
const API_CACHE_NAME = 'weekly-star-tracker-api-v2';
const CHALLENGES_CACHE_NAME = 'weekly-star-tracker-challenges-v1';

// Files to cache for offline functionality
const STATIC_CACHE_URLS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  // Add more static assets as needed
];

// API endpoints to cache for offline functionality
const API_CACHE_URLS = [
  '/api/progress',
  '/api/tasks',
  '/api/rewards',
  '/api/cache/preload',  // New preload endpoint
];

// Challenge storage for offline usage
let challengeCache = null;
const CACHE_EXPIRY_HOURS = 24;

// Install event - cache essential files and preload challenges
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache static files
      caches.open(CACHE_NAME)
        .then((cache) => {
          console.log('📦 Caching static files');
          return cache.addAll(STATIC_CACHE_URLS.map(url => new Request(url, {credentials: 'same-origin'})));
        }),
      
      // Preload challenges for offline usage
      preloadChallenges()
    ]).then(() => {
      console.log('✅ Service Worker installed successfully');
      self.skipWaiting();
    }).catch((error) => {
      console.error('❌ Service Worker installation failed:', error);
    })
  );
});

// Function to preload challenges
async function preloadChallenges() {
  try {
    console.log('📚 Preloading challenges for offline usage...');
    
    const response = await fetch('/api/cache/preload', {
      method: 'GET',
      credentials: 'same-origin'
    });
    
    if (response.ok) {
      const data = await response.json();
      challengeCache = {
        ...data.cached_challenges,
        timestamp: new Date().toISOString(),
        expires: new Date(Date.now() + CACHE_EXPIRY_HOURS * 60 * 60 * 1000).toISOString()
      };
      
      // Store in cache
      const cache = await caches.open(CHALLENGES_CACHE_NAME);
      await cache.put('/offline-challenges', new Response(JSON.stringify(challengeCache)));
      
      console.log(`✅ Preloaded ${data.total_problems} challenges for offline usage`);
    }
  } catch (error) {
    console.error('⚠️  Failed to preload challenges:', error);
  }
}

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('✅ Service Worker activating...');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
              console.log('🗑️ Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // Take control of all clients
      self.clients.claim()
    ])
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
  }
  // Handle static file requests
  else {
    event.respondWith(handleStaticRequest(request));
  }
});

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  // Handle challenge creation with offline fallback
  if (url.pathname.includes('/challenge/') && request.method === 'POST') {
    try {
      const networkResponse = await fetch(request);
      if (networkResponse.ok) {
        return networkResponse;
      }
      throw new Error('Network request failed');
    } catch (error) {
      console.log('🔄 Network unavailable, serving cached challenges...');
      return await serveCachedChallenge(url);
    }
  }
  
  // For read-only requests (GET), try network first, then cache
  if (request.method === 'GET') {
    try {
      const networkResponse = await fetch(request);
      
      if (networkResponse.ok) {
        // Cache successful responses
        const cache = await caches.open(API_CACHE_NAME);
        cache.put(request, networkResponse.clone());
        return networkResponse;
      }
      throw new Error('Network response not ok');
    } catch (error) {
      console.log('🔄 Network unavailable, serving from cache...');
      
      // Try to serve from cache
      const cache = await caches.open(API_CACHE_NAME);
      const cachedResponse = await cache.match(request);
      
      if (cachedResponse) {
        return cachedResponse;
      }
      
      // If no cached response, return error
      return new Response(JSON.stringify({
        success: false,
        error: 'Network unavailable',
        message: 'Please check your internet connection and try again.',
        offline: true
      }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
  
  // For other methods (POST, PUT, DELETE), require network
  return fetch(request);
}

// Serve cached challenges when offline
async function serveCachedChallenge(url) {
  try {
    const cache = await caches.open(CHALLENGES_CACHE_NAME);
    const cachedData = await cache.match('/offline-challenges');
    
    if (!cachedData) {
      return new Response(JSON.stringify({
        success: false,
        error: 'No cached challenges available',
        message: 'Please connect to internet to load new challenges.'
      }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    const challengeData = await cachedData.json();
    
    // Check if cache is expired
    if (new Date() > new Date(challengeData.expires)) {
      console.warn('⚠️  Cached challenges expired, but serving anyway due to offline mode');
    }
    
    // Extract challenge type and grade from URL
    const pathParts = url.pathname.split('/');
    const challengeType = pathParts[2]; // math, german, english
    const grade = pathParts[4]; // grade number
    
    let problems = [];
    
    if (challengeType === 'math' && challengeData.math && challengeData.math[`grade_${grade}`]) {
      const mathProblems = challengeData.math[`grade_${grade}`];
      // Mix different problem types
      Object.values(mathProblems).forEach(typeProblems => {
        if (Array.isArray(typeProblems)) {
          problems = problems.concat(typeProblems.slice(0, 3)); // Take first 3 of each type
        }
      });
    } else if (challengeType === 'german' && challengeData.german && challengeData.german[`grade_${grade}`]) {
      const germanProblems = challengeData.german[`grade_${grade}`];
      Object.values(germanProblems).forEach(typeProblems => {
        if (Array.isArray(typeProblems)) {
          problems = problems.concat(typeProblems.slice(0, 3));
        }
      });
    } else if (challengeType === 'english' && challengeData.english && challengeData.english[`grade_${grade}`]) {
      const englishProblems = challengeData.english[`grade_${grade}`];
      Object.values(englishProblems).forEach(typeProblems => {
        if (Array.isArray(typeProblems)) {
          problems = problems.concat(typeProblems.slice(0, 3));
        }
      });
    }
    
    if (problems.length === 0) {
      return new Response(JSON.stringify({
        success: false,
        error: 'No cached challenges for this type/grade',
        message: 'Please connect to internet to load challenges.'
      }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Create offline challenge response
    const challenge = {
      id: 'offline-' + Date.now(),
      grade: parseInt(grade),
      problems: problems,
      created_at: new Date().toISOString(),
      offline: true
    };
    
    return new Response(JSON.stringify({
      challenge: challenge,
      success: true,
      message: `Offline ${challengeType} challenge loaded with ${problems.length} problems`,
      offline: true
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
    
  } catch (error) {
    console.error('❌ Error serving cached challenge:', error);
    return new Response(JSON.stringify({
      success: false,
      error: 'Failed to load offline challenges',
      message: 'Please check your internet connection and try again.'
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Handle static requests with cache-first strategy
async function handleStaticRequest(request) {
  // Try cache first
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // Try network
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful responses
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // For navigation requests, return cached index.html
    if (request.mode === 'navigate') {
      const cachedIndex = await caches.match('/');
      if (cachedIndex) {
        return cachedIndex;
      }
    }
    
    // Return offline page or error
    return new Response(
      `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Weekly Star Tracker - Offline</title>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body { 
              font-family: system-ui, -apple-system, sans-serif; 
              text-align: center; 
              padding: 40px 20px; 
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white;
              min-height: 100vh;
              display: flex;
              align-items: center;
              justify-content: center;
              flex-direction: column;
            }
            .offline-container {
              background: rgba(255,255,255,0.1);
              padding: 40px;
              border-radius: 20px;
              backdrop-filter: blur(10px);
            }
            h1 { margin-bottom: 20px; }
            p { font-size: 18px; line-height: 1.6; }
            .star { font-size: 48px; margin-bottom: 20px; }
          </style>
        </head>
        <body>
          <div class="offline-container">
            <div class="star">⭐</div>
            <h1>Weekly Star Tracker</h1>
            <p>Sie sind momentan offline.</p>
            <p>Bitte überprüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.</p>
            <button onclick="location.reload()" style="
              background: #4f46e5; 
              color: white; 
              border: none; 
              padding: 12px 24px; 
              border-radius: 8px; 
              font-size: 16px; 
              margin-top: 20px;
              cursor: pointer;
            ">
              🔄 Erneut versuchen
            </button>
          </div>
        </body>
      </html>
      `,
      { 
        headers: { 'Content-Type': 'text/html' },
        status: 503 
      }
    );
  }
}

// Handle background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('🔄 Background sync triggered:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  console.log('📡 Attempting background sync...');
  // Here you could implement queued actions that should be synced when online
}

// Handle push notifications (for future use)
self.addEventListener('push', (event) => {
  console.log('🔔 Push notification received');
  
  const options = {
    body: event.data ? event.data.text() : 'Neue Benachrichtigung von Weekly Star Tracker',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'App öffnen',
        icon: '/icons/icon-192x192.png'
      },
      {
        action: 'close',
        title: 'Schließen'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('Weekly Star Tracker', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('🔔 Notification clicked:', event.action);
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      self.clients.openWindow('/')
    );
  }
});

console.log('🚀 Weekly Star Tracker Service Worker loaded successfully!');