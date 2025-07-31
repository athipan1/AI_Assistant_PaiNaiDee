import { useState, useCallback, useRef } from 'react';
import { AIService } from '../services/AIService';
import { SpeechService } from '../services/SpeechService';
import { LocationService } from '../services/LocationService';
import { HapticService } from '../services/HapticService';
import { VoiceCommand, AIResponse, Location, Place } from '../types';

export const useAIVoiceAssistant = () => {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentLocation, setCurrentLocation] = useState<Location | null>(null);
  const [places, setPlaces] = useState<Place[]>([]);
  const [lastResponse, setLastResponse] = useState<AIResponse | null>(null);
  const [language, setLanguage] = useState<'th' | 'en'>('th');

  const aiService = useRef(new AIService());
  const speechService = useRef(new SpeechService());
  const locationService = useRef(new LocationService());

  // Initialize location tracking
  const initializeLocation = useCallback(async () => {
    try {
      const location = await locationService.current.getCurrentLocation();
      if (location) {
        setCurrentLocation(location);
        // Start watching location changes
        locationService.current.watchLocation((newLocation) => {
          setCurrentLocation(newLocation);
        });
      }
    } catch (error) {
      console.error('Location initialization error:', error);
    }
  }, []);

  // Start listening for voice commands
  const startListening = useCallback(async () => {
    try {
      setIsListening(true);
      HapticService.light();
      
      const recording = await speechService.current.startListening();
      if (!recording) {
        throw new Error('Failed to start recording');
      }
    } catch (error) {
      console.error('Start listening error:', error);
      setIsListening(false);
      HapticService.error();
    }
  }, []);

  // Stop listening and process command
  const stopListening = useCallback(async () => {
    try {
      setIsListening(false);
      setIsProcessing(true);
      HapticService.medium();

      const voiceCommand = await speechService.current.stopListening();
      if (!voiceCommand) {
        throw new Error('No voice command captured');
      }

      // Process the command with AI
      const response = await aiService.current.processVoiceCommand({
        ...voiceCommand,
        language,
      });

      setLastResponse(response);

      // If places were found, trigger haptic feedback
      if (response.places && response.places.length > 0) {
        setPlaces(response.places);
        HapticService.placeRecommendation();
      }

      // Speak the response
      if (response.text) {
        await speakResponse(response.text);
      }

    } catch (error) {
      console.error('Stop listening error:', error);
      HapticService.error();
      
      // Speak error message
      const errorMessage = language === 'th' 
        ? 'ขอโทษครับ มีปัญหาในการประมวลผลเสียง'
        : 'Sorry, there was an error processing your voice.';
      await speakResponse(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  }, [language]);

  // Speak AI response
  const speakResponse = useCallback(async (text: string) => {
    try {
      setIsSpeaking(true);
      HapticService.aiResponse();
      
      const speechLanguage = language === 'th' ? 'th-TH' : 'en-US';
      await speechService.current.speak(text, speechLanguage);
    } catch (error) {
      console.error('Speech synthesis error:', error);
    } finally {
      setIsSpeaking(false);
    }
  }, [language]);

  // Get nearby places manually
  const getNearbyPlaces = useCallback(async (query: string = '') => {
    try {
      if (!currentLocation) {
        await initializeLocation();
        return;
      }

      const nearbyPlaces = await locationService.current.getNearbyPlaces(
        currentLocation,
        query
      );
      
      setPlaces(nearbyPlaces);
      
      if (nearbyPlaces.length > 0) {
        HapticService.placeRecommendation();
      }

      return nearbyPlaces;
    } catch (error) {
      console.error('Get nearby places error:', error);
      return [];
    }
  }, [currentLocation, initializeLocation]);

  // Handle place selection
  const selectPlace = useCallback(async (place: Place) => {
    try {
      HapticService.selection();
      
      // Create a natural language response about the selected place
      const response = language === 'th'
        ? `คุณเลือก ${place.name} ${place.description} อยู่ห่างจากคุณ ${place.distance?.toFixed(1)} กิโลเมตร`
        : `You selected ${place.name}. ${place.description}. It's ${place.distance?.toFixed(1)} kilometers away from you.`;

      await speakResponse(response);
    } catch (error) {
      console.error('Place selection error:', error);
    }
  }, [language, speakResponse]);

  // Toggle language
  const toggleLanguage = useCallback(() => {
    const newLanguage = language === 'th' ? 'en' : 'th';
    setLanguage(newLanguage);
    
    // Save preference
    aiService.current.saveUserPreferences({ language: newLanguage });
    
    // Announce language change
    const announcement = newLanguage === 'th' 
      ? 'เปลี่ยนเป็นภาษาไทยแล้ว'
      : 'Language changed to English';
    speakResponse(announcement);
  }, [language, speakResponse]);

  // Stop all audio
  const stopSpeaking = useCallback(() => {
    speechService.current.stop();
    setIsSpeaking(false);
  }, []);

  // Quick commands
  const executeQuickCommand = useCallback(async (command: string) => {
    const voiceCommand: VoiceCommand = {
      text: command,
      confidence: 1.0,
      language,
    };

    try {
      setIsProcessing(true);
      const response = await aiService.current.processVoiceCommand(voiceCommand);
      setLastResponse(response);

      if (response.places && response.places.length > 0) {
        setPlaces(response.places);
        HapticService.placeRecommendation();
      }

      if (response.text) {
        await speakResponse(response.text);
      }
    } catch (error) {
      console.error('Quick command error:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [language, speakResponse]);

  return {
    // State
    isListening,
    isProcessing,
    isSpeaking,
    currentLocation,
    places,
    lastResponse,
    language,

    // Actions
    startListening,
    stopListening,
    speakResponse,
    getNearbyPlaces,
    selectPlace,
    toggleLanguage,
    stopSpeaking,
    executeQuickCommand,
    initializeLocation,
  };
};