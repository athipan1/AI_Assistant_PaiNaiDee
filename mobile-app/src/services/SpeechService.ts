import * as Speech from 'expo-speech';
import { Audio } from 'expo-av';
import { VoiceCommand } from '../types';

export class SpeechService {
  private recording: Audio.Recording | null = null;

  async speak(text: string, language: string = 'th-TH'): Promise<void> {
    try {
      // Configure speech options
      const options: Speech.SpeechOptions = {
        language: language,
        pitch: 1.0,
        rate: 0.8,
        quality: Speech.VoiceQuality.Enhanced,
      };

      await Speech.speak(text, options);
    } catch (error) {
      console.error('Speech synthesis error:', error);
    }
  }

  async startListening(): Promise<Audio.Recording | null> {
    try {
      // Request microphone permissions
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        throw new Error('Microphone permission not granted');
      }

      // Configure audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Start recording
      this.recording = new Audio.Recording();
      const recordingOptions = {
        android: {
          extension: '.m4a',
          outputFormat: Audio.RECORDING_FORMAT_MPEG_4_AAC,
          audioEncoder: Audio.RECORDING_OPTION_ANDROID_AUDIO_ENCODER_AAC,
          sampleRate: 44100,
          numberOfChannels: 2,
          bitRate: 128000,
        },
        ios: {
          extension: '.wav',
          audioQuality: Audio.RECORDING_OPTION_IOS_AUDIO_QUALITY_HIGH,
          sampleRate: 44100,
          numberOfChannels: 2,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
      };

      await this.recording.prepareToRecordAsync(recordingOptions);
      await this.recording.startAsync();
      
      return this.recording;
    } catch (error) {
      console.error('Error starting recording:', error);
      return null;
    }
  }

  async stopListening(): Promise<VoiceCommand | null> {
    try {
      if (!this.recording) {
        return null;
      }

      await this.recording.stopAndUnloadAsync();
      const uri = this.recording.getURI();
      this.recording = null;

      if (!uri) {
        return null;
      }

      // For demo purposes, we'll simulate speech-to-text
      // In a real app, you would send the audio to Google STT or Whisper
      const mockTranscription = await this.simulateSpeechToText(uri);
      
      return {
        text: mockTranscription,
        confidence: 0.9,
        language: 'th',
      };
    } catch (error) {
      console.error('Error stopping recording:', error);
      return null;
    }
  }

  private async simulateSpeechToText(audioUri: string): Promise<string> {
    // This is a mock implementation
    // In a real app, you would integrate with Google Speech-to-Text or Whisper
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Return mock transcription
    const mockPhrases = [
      'หาร้านอาหารใกล้ฉัน',
      'แนะนำสถานที่ท่องเที่ยวในกรุงเทพ',
      'โรงแรมดีๆ ในเชียงใหม่',
      'วัดสวยๆ ที่ควรไป',
      'Find restaurants near me',
      'Recommend tourist attractions in Bangkok',
      'Good hotels in Chiang Mai',
      'Beautiful temples to visit'
    ];
    
    return mockPhrases[Math.floor(Math.random() * mockPhrases.length)];
  }

  async integrateGoogleSTT(audioUri: string, apiKey: string): Promise<string> {
    try {
      // This would be the real Google Speech-to-Text integration
      // For now, returning mock data
      
      const formData = new FormData();
      formData.append('audio', {
        uri: audioUri,
        type: 'audio/wav',
        name: 'recording.wav',
      } as any);

      const response = await fetch('https://speech.googleapis.com/v1/speech:recognize', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'multipart/form-data',
        },
        body: formData,
      });

      const result = await response.json();
      return result.results?.[0]?.alternatives?.[0]?.transcript || '';
    } catch (error) {
      console.error('Google STT Error:', error);
      return '';
    }
  }

  stop(): void {
    Speech.stop();
  }

  isSpeaking(): boolean {
    return Speech.isSpeakingAsync() as any;
  }
}