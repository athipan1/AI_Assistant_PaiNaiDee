import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  StatusBar,
  Alert,
  SafeAreaView,
} from 'react-native';
import { useAIVoiceAssistant } from '../hooks/useAIVoiceAssistant';
import VoiceControls from '../components/VoiceControls';
import PlaceList from '../components/PlaceList';
import AR3DView from '../components/AR3DView';
import { Place } from '../types';

const AIVoiceAssistantScreen: React.FC = () => {
  const {
    isListening,
    isProcessing,
    isSpeaking,
    currentLocation,
    places,
    lastResponse,
    language,
    startListening,
    stopListening,
    selectPlace,
    toggleLanguage,
    stopSpeaking,
    executeQuickCommand,
    initializeLocation,
  } = useAIVoiceAssistant();

  const [showARView, setShowARView] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState<string>('neutral');

  useEffect(() => {
    // Initialize location on component mount
    initializeLocation();
  }, [initializeLocation]);

  useEffect(() => {
    // Update emotion from AI response
    if (lastResponse?.emotion) {
      setCurrentEmotion(lastResponse.emotion);
    }
  }, [lastResponse]);

  const handlePlaceSelect = async (place: Place) => {
    await selectPlace(place);
    // You could navigate to a detailed view or show more info
    Alert.alert(
      place.name,
      `${place.description}\n\n${language === 'th' ? 'ระยะทาง' : 'Distance'}: ${place.distance?.toFixed(1)} km\n${language === 'th' ? 'คะแนน' : 'Rating'}: ${place.rating}/5`,
      [
        { text: language === 'th' ? 'ตกลง' : 'OK' },
      ]
    );
  };

  const quickCommands = [
    {
      th: 'หาร้านอาหารใกล้ฉัน',
      en: 'Find restaurants near me',
      icon: '🍽️',
    },
    {
      th: 'แนะนำสถานที่ท่องเที่ยว',
      en: 'Recommend tourist attractions',
      icon: '🎯',
    },
    {
      th: 'หาโรงแรมใกล้เคียง',
      en: 'Find nearby hotels',
      icon: '🏨',
    },
    {
      th: 'วัดสวยๆ ที่ควรไป',
      en: 'Beautiful temples to visit',
      icon: '🏛️',
    },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1976D2" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>
          {language === 'th' ? 'ไปไหนดี AI Assistant' : 'PaiNaiDee AI Assistant'}
        </Text>
        <View style={styles.headerControls}>
          <TouchableOpacity
            style={styles.arToggle}
            onPress={() => setShowARView(!showARView)}
          >
            <Text style={styles.arToggleText}>
              {showARView ? '📱' : '👾'}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.languageToggle}
            onPress={toggleLanguage}
          >
            <Text style={styles.languageText}>
              {language === 'th' ? 'TH' : 'EN'}
            </Text>
          </TouchableOpacity>
          {isSpeaking && (
            <TouchableOpacity
              style={styles.stopButton}
              onPress={stopSpeaking}
            >
              <Text style={styles.stopButtonText}>🔇</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Location Status */}
        {currentLocation && (
          <View style={styles.locationStatus}>
            <Text style={styles.locationText}>
              📍 {language === 'th' ? 'ตำแหน่งปัจจุบัน' : 'Current Location'}: {' '}
              {currentLocation.latitude.toFixed(4)}, {currentLocation.longitude.toFixed(4)}
            </Text>
          </View>
        )}

        {/* 3D AR View */}
        {showARView && (
          <View style={styles.arContainer}>
            <AR3DView 
              emotion={currentEmotion}
              gesture={lastResponse?.gesture}
              onModelLoad={() => console.log('3D model loaded')}
            />
          </View>
        )}

        {/* AI Response */}
        {lastResponse && (
          <View style={styles.responseContainer}>
            <Text style={styles.responseTitle}>
              {language === 'th' ? '🤖 AI ตอบ:' : '🤖 AI Response:'}
            </Text>
            <Text style={styles.responseText}>{lastResponse.text}</Text>
            {lastResponse.emotion && (
              <Text style={styles.emotionText}>
                {language === 'th' ? 'อารมณ์' : 'Emotion'}: {lastResponse.emotion}
                {getEmotionEmoji(lastResponse.emotion)}
              </Text>
            )}
          </View>
        )}

        {/* Voice Controls */}
        <VoiceControls
          isListening={isListening}
          isProcessing={isProcessing}
          onStartListening={startListening}
          onStopListening={stopListening}
          language={language}
        />

        {/* Quick Commands */}
        <View style={styles.quickCommandsContainer}>
          <Text style={styles.quickCommandsTitle}>
            {language === 'th' ? '⚡ คำสั่งด่วน' : '⚡ Quick Commands'}
          </Text>
          <View style={styles.quickCommandsGrid}>
            {quickCommands.map((command, index) => (
              <TouchableOpacity
                key={index}
                style={styles.quickCommandButton}
                onPress={() => executeQuickCommand(command[language])}
                disabled={isProcessing}
              >
                <Text style={styles.quickCommandIcon}>{command.icon}</Text>
                <Text style={styles.quickCommandText}>
                  {command[language]}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Places List */}
        {places.length > 0 && (
          <PlaceList
            places={places}
            onPlaceSelect={handlePlaceSelect}
            language={language}
          />
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const getEmotionEmoji = (emotion: string): string => {
  const emojiMap: { [key: string]: string } = {
    happy: ' 😊',
    excited: ' 🤩',
    worried: ' 😟',
    calm: ' 😌',
    neutral: ' 😐',
    sad: ' 😢',
    angry: ' 😠',
  };
  return emojiMap[emotion] || ' 😐';
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#1976D2',
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  headerTitle: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
    flex: 1,
  },
  headerControls: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  arToggle: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginRight: 8,
  },
  arToggleText: {
    fontSize: 18,
  },
  languageToggle: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginRight: 8,
  },
  languageText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },
  stopButton: {
    backgroundColor: '#f44336',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  stopButtonText: {
    fontSize: 16,
  },
  content: {
    flex: 1,
  },
  locationStatus: {
    backgroundColor: 'white',
    padding: 12,
    marginVertical: 4,
  },
  locationText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  arContainer: {
    height: 300,
    backgroundColor: 'black',
    marginVertical: 8,
  },
  responseContainer: {
    backgroundColor: 'white',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  responseTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  responseText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 8,
  },
  emotionText: {
    fontSize: 12,
    color: '#2196F3',
    fontStyle: 'italic',
  },
  quickCommandsContainer: {
    margin: 16,
  },
  quickCommandsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  quickCommandsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickCommandButton: {
    backgroundColor: 'white',
    width: '48%',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  quickCommandIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  quickCommandText: {
    fontSize: 12,
    color: '#333',
    textAlign: 'center',
    fontWeight: '500',
  },
});

export default AIVoiceAssistantScreen;