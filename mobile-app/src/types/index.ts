export interface Location {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

export interface Place {
  id: string;
  name: string;
  description: string;
  location: Location;
  distance?: number;
  rating?: number;
  category: string;
  photoUrl?: string;
}

export interface VoiceCommand {
  text: string;
  confidence: number;
  language: string;
}

export interface AIResponse {
  text: string;
  action?: string;
  places?: Place[];
  emotion?: string;
  gesture?: string;
}

export interface User {
  id: string;
  preferences: {
    language: 'th' | 'en';
    interests: string[];
  };
}