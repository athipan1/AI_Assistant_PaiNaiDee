# PaiNaiDee AI Voice Assistant Mobile App

A React Native + Expo mobile application that provides AI-powered voice assistance for Thai tourism, featuring speech-to-text, location services, 3D visualization, and haptic feedback.

## Features

### ✅ Core Requirements Implemented
- **React Native + Expo**: Built with Expo SDK for cross-platform mobile development
- **Speech-to-Text**: Voice command recognition with Google STT integration ready
- **Location Access**: Real-time location tracking and nearby place detection
- **3D AR Scene**: Three.js-based 3D visualization with emotion-responsive animations
- **AI Voice Responses**: Text-to-speech synthesis in Thai and English
- **Haptic Feedback**: Vibration patterns for place recommendations and interactions
- **Thai NLP Support**: Full Thai language processing and responses

### 🎯 Key Features
- **Voice Commands**: Natural language processing for tourism queries
- **Emotion Analysis**: AI detects user emotions and adapts responses
- **Nearby Places**: Location-based recommendations for restaurants, temples, hotels
- **3D Visualization**: Interactive 3D scenes that respond to emotions
- **Bilingual Support**: Seamless switching between Thai and English
- **Quick Commands**: Preset buttons for common tourism queries
- **Real-time Updates**: Live location tracking and place updates

## Prerequisites

- Node.js 18+ 
- Expo CLI: `npm install -g @expo/cli`
- Expo Go app on your mobile device
- Backend server running (see main project README)

## Installation

1. **Navigate to mobile app directory**:
   ```bash
   cd mobile-app
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure backend URL**:
   Edit `src/config/index.ts` and update `API_BASE_URL` to your backend server IP:
   ```typescript
   API_BASE_URL: 'http://YOUR_BACKEND_IP:8000'
   ```

4. **Start the development server**:
   ```bash
   npm start
   ```

5. **Run on device**:
   - Install Expo Go app on your phone
   - Scan the QR code displayed in terminal
   - Or use: `npm run android` / `npm run ios`

## Backend Configuration

The mobile app connects to the PaiNaiDee backend server. Make sure the backend is running:

```bash
# In the main project directory
cd painaidee_ai_assistant
python main.py
```

Update the mobile app's configuration to point to your backend:
```typescript
// src/config/index.ts
API_BASE_URL: 'http://192.168.1.100:8000' // Your backend IP
```

## Usage

### Voice Commands
1. **Tap the microphone button** to start listening
2. **Speak your command** in Thai or English:
   - "หาร้านอาหารใกล้ฉัน" (Find restaurants near me)
   - "แนะนำสถานที่ท่องเที่ยวในกรุงเทพ" (Recommend attractions in Bangkok)
   - "วัดสวยๆ ที่ควรไป" (Beautiful temples to visit)
3. **AI responds with voice** and shows relevant places
4. **Feel haptic feedback** when places are recommended

### Quick Commands
- Use preset buttons for common queries
- Toggle between Thai/English languages
- View 3D visualization of AI emotions

### 3D AR View
- Toggle 3D view with the AR button
- 3D objects respond to detected emotions
- Interactive animations based on AI responses

## Project Structure

```
mobile-app/
├── src/
│   ├── components/          # React components
│   │   ├── AR3DView.tsx     # 3D visualization
│   │   ├── PlaceList.tsx    # Place recommendations
│   │   └── VoiceControls.tsx # Voice interface
│   ├── hooks/               # Custom React hooks
│   │   └── useAIVoiceAssistant.ts # Main AI logic
│   ├── screens/             # App screens
│   │   └── AIVoiceAssistantScreen.tsx # Main screen
│   ├── services/            # Service classes
│   │   ├── AIService.ts     # AI/Backend integration
│   │   ├── SpeechService.ts # Speech-to-text/TTS
│   │   ├── LocationService.ts # GPS/Places
│   │   └── HapticService.ts # Vibration feedback
│   ├── types/               # TypeScript types
│   │   └── index.ts         # Common interfaces
│   └── config/              # Configuration
│       └── index.ts         # App configuration
├── App.tsx                  # Main app component
├── app.json                 # Expo configuration
└── package.json             # Dependencies
```

## API Integration

The app integrates with the backend APIs:

- **AI Model Selection**: `/ai/select_model_with_emotion`
- **Tourism Recommendations**: `/tourism/recommendations/integrated`
- **Action Plans**: `/action/quick_action`
- **Emotion Analysis**: `/emotion/analyze_emotion`

## Permissions

The app requires the following permissions:

### Android
- `RECORD_AUDIO`: For voice commands
- `ACCESS_FINE_LOCATION`: For nearby places
- `VIBRATE`: For haptic feedback

### iOS
- `NSMicrophoneUsageDescription`: For voice commands
- `NSLocationWhenInUseUsageDescription`: For nearby places

## Customization

### Adding New Voice Commands
1. Update `quickCommands` array in `AIVoiceAssistantScreen.tsx`
2. Add command processing logic in `AIService.ts`

### Modifying 3D Scenes
1. Edit `AR3DView.tsx` to add new 3D models
2. Update emotion-based animations
3. Add new Three.js geometries and materials

### Adding New Languages
1. Update `Config.SPEECH.SUPPORTED_LANGUAGES`
2. Add language-specific responses in services
3. Update UI text translations

## Development

### Running Tests
```bash
npm test
```

### Building for Production
```bash
# Build APK
expo build:android

# Build IPA  
expo build:ios
```

### Debugging
- Use Expo DevTools for debugging
- Check React Native debugger
- Monitor backend logs for API issues

## Troubleshooting

### Common Issues

1. **Backend connection failed**:
   - Check backend is running on correct port
   - Update `API_BASE_URL` in config
   - Ensure devices are on same network

2. **Voice recognition not working**:
   - Grant microphone permissions
   - Test with simple English commands first
   - Check speech service logs

3. **Location not found**:
   - Grant location permissions
   - Enable location services on device
   - Test outdoors for better GPS signal

4. **3D view not rendering**:
   - Check device WebGL support
   - Update Expo SDK version
   - Test on different device

### Performance Tips
- Close other apps when using voice features
- Use Wi-Fi for better API response times
- Keep app in foreground during voice commands

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on real devices
5. Submit a pull request

## License

This project is part of the PaiNaiDee AI Assistant system, licensed under MIT License.

---

**Made with ❤️ for Thai tourism and AI innovation**