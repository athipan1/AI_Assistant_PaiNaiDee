// Configuration for the AI Voice Assistant
export const Config = {
  // Backend API configuration
  API_BASE_URL: 'http://192.168.1.100:8000', // Change this to your backend IP
  
  // Speech configuration
  SPEECH: {
    DEFAULT_LANGUAGE: 'th-TH',
    SUPPORTED_LANGUAGES: {
      th: 'th-TH',
      en: 'en-US',
    },
    SPEECH_RATE: 0.8,
    SPEECH_PITCH: 1.0,
  },

  // Location configuration
  LOCATION: {
    ACCURACY: 'high' as const,
    UPDATE_INTERVAL: 5000, // 5 seconds
    DISTANCE_THRESHOLD: 10, // 10 meters
  },

  // 3D/AR configuration
  AR: {
    DEFAULT_CAMERA_POSITION: [0, 0, 5],
    ANIMATION_SPEED: 0.01,
    PARTICLE_COUNT: 100,
  },

  // Thai language support
  THAI_NLP: {
    ENABLED: true,
    FALLBACK_TO_ENGLISH: true,
  },

  // Feature flags
  FEATURES: {
    SPEECH_TO_TEXT: true,
    TEXT_TO_SPEECH: true,
    HAPTIC_FEEDBACK: true,
    LOCATION_SERVICES: true,
    AR_3D_SCENE: true,
    THAI_LANGUAGE: true,
    NEARBY_PLACES: true,
  },

  // Demo mode (for testing without backend)
  DEMO_MODE: false,
};

// Helper function to get API URL
export const getApiUrl = (endpoint: string): string => {
  return `${Config.API_BASE_URL}${endpoint}`;
};

// Helper function to check feature availability
export const isFeatureEnabled = (feature: keyof typeof Config.FEATURES): boolean => {
  return Config.FEATURES[feature];
};