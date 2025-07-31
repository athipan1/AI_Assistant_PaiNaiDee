import AsyncStorage from '@react-native-async-storage/async-storage';
import { AIResponse, VoiceCommand } from '../types';
import { getApiUrl } from '../config';

export class AIService {
  async processVoiceCommand(command: VoiceCommand): Promise<AIResponse> {
    try {
      // First, analyze emotion and get AI response
      const emotionResponse = await fetch(getApiUrl('/ai/select_model_with_emotion'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: command.text,
          analyze_emotion: true,
          language: command.language,
        }),
      });

      const emotionData = await emotionResponse.json();

      // Get tourism recommendations if the command is about places
      let places = [];
      if (this.isLocationQuery(command.text)) {
        const location = await this.getCurrentLocation();
        if (location) {
          const tourismResponse = await fetch(getApiUrl('/tourism/recommendations/integrated'), {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              user_id: 'mobile_user',
              query: command.text,
              context: {
                location: location,
                language: command.language,
              },
            }),
          });

          if (tourismResponse.ok) {
            const tourismData = await tourismResponse.json();
            places = tourismData.recommendations || [];
          }
        }
      }

      // Generate action plan for multimodal response
      const actionResponse = await fetch(getApiUrl('/action/quick_action'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          intent: command.text,
          context: {
            emotion: emotionData.emotion_analysis?.primary_emotion,
            places_found: places.length > 0,
          },
        }),
      });

      const actionData = await actionResponse.json();

      return {
        text: this.generateResponse(command.text, emotionData, places, command.language),
        emotion: emotionData.emotion_analysis?.primary_emotion,
        gesture: emotionData.emotion_analysis?.suggested_gesture,
        places: places,
        action: actionData.action_plan?.speech?.text,
      };
    } catch (error) {
      console.error('AI Service Error:', error);
      return {
        text: command.language === 'th' 
          ? 'ขอโทษครับ มีปัญหาในการติดต่อเซิร์ฟเวอร์'
          : 'Sorry, there was an error connecting to the server.',
      };
    }
  }

  private isLocationQuery(text: string): boolean {
    const locationKeywords = [
      // English
      'place', 'restaurant', 'hotel', 'temple', 'attraction', 'nearby', 'near me',
      'where', 'location', 'visit', 'go to', 'find',
      // Thai
      'ที่ไหน', 'ร้าน', 'โรงแรม', 'วัด', 'สถานที่', 'ใกล้', 'แนะนำ', 'ไป', 'หา'
    ];
    
    return locationKeywords.some(keyword => 
      text.toLowerCase().includes(keyword.toLowerCase())
    );
  }

  private async getCurrentLocation() {
    try {
      // This will be implemented with actual location service
      return {
        latitude: 13.7563,
        longitude: 100.5018, // Bangkok coordinates as default
      };
    } catch (error) {
      console.error('Location Error:', error);
      return null;
    }
  }

  private generateResponse(
    originalText: string,
    emotionData: any,
    places: any[],
    language: string
  ): string {
    const isThaiLanguage = language === 'th';
    
    if (places.length > 0) {
      const placeNames = places.slice(0, 3).map(p => p.name).join(', ');
      return isThaiLanguage
        ? `ผมเจอสถานที่ที่น่าสนใจให้คุณแล้ว: ${placeNames} คุณต้องการข้อมูลเพิ่มเติมไหมครับ?`
        : `I found some interesting places for you: ${placeNames}. Would you like more information?`;
    }

    // Default responses based on emotion
    const emotion = emotionData.emotion_analysis?.primary_emotion || 'neutral';
    
    if (isThaiLanguage) {
      switch (emotion) {
        case 'excited':
          return 'ว้าว! คุณดูตื่นเต้นมากเลยนะครับ ผมจะช่วยหาข้อมูลที่น่าสนใจให้คุณ';
        case 'worried':
          return 'ไม่ต้องกังวลครับ ผมจะช่วยคุณหาข้อมูลที่ดีที่สุด';
        case 'happy':
          return 'ดีใจที่เห็นคุณมีความสุขครับ มีอะไรให้ผมช่วยไหม?';
        default:
          return 'สวัสดีครับ ผมเป็นผู้ช่วย AI สำหรับการท่องเที่ยว มีอะไรให้ช่วยไหมครับ?';
      }
    } else {
      switch (emotion) {
        case 'excited':
          return 'Wow! You seem very excited! Let me help you find something amazing.';
        case 'worried':
          return "Don't worry, I'm here to help you find the best information.";
        case 'happy':
          return "I'm happy to see you're in a good mood! How can I assist you?";
        default:
          return "Hello! I'm your AI tourism assistant. How can I help you today?";
      }
    }
  }

  async saveUserPreferences(preferences: any) {
    try {
      await AsyncStorage.setItem('userPreferences', JSON.stringify(preferences));
    } catch (error) {
      console.error('Error saving preferences:', error);
    }
  }

  async getUserPreferences() {
    try {
      const preferences = await AsyncStorage.getItem('userPreferences');
      return preferences ? JSON.parse(preferences) : null;
    } catch (error) {
      console.error('Error getting preferences:', error);
      return null;
    }
  }
}