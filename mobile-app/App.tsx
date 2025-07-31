import React from 'react';
import { StatusBar } from 'expo-status-bar';
import AIVoiceAssistantScreen from './src/screens/AIVoiceAssistantScreen';

export default function App() {
  return (
    <>
      <AIVoiceAssistantScreen />
      <StatusBar style="light" />
    </>
  );
}
