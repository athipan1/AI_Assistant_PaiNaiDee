import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Animated } from 'react-native';

interface VoiceControlsProps {
  isListening: boolean;
  isProcessing: boolean;
  onStartListening: () => void;
  onStopListening: () => void;
  language: 'th' | 'en';
}

const VoiceControls: React.FC<VoiceControlsProps> = ({
  isListening,
  isProcessing,
  onStartListening,
  onStopListening,
  language,
}) => {
  const pulseAnim = React.useRef(new Animated.Value(1)).current;

  React.useEffect(() => {
    if (isListening) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();
      return () => pulse.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isListening]);

  const getButtonText = () => {
    if (isProcessing) {
      return language === 'th' ? 'กำลังประมวลผล...' : 'Processing...';
    }
    if (isListening) {
      return language === 'th' ? 'กดเพื่อหยุดฟัง' : 'Tap to stop';
    }
    return language === 'th' ? 'กดเพื่อพูด' : 'Tap to speak';
  };

  const getStatusText = () => {
    if (isProcessing) {
      return language === 'th' 
        ? 'AI กำลังวิเคราะห์คำพูดของคุณ...'
        : 'AI is analyzing your speech...';
    }
    if (isListening) {
      return language === 'th' 
        ? 'กำลังฟังคำสั่งของคุณ...'
        : 'Listening to your command...';
    }
    return language === 'th' 
      ? 'พร้อมรับฟังคำสั่งของคุณ'
      : 'Ready to listen to your command';
  };

  return (
    <View style={styles.container}>
      <Text style={styles.statusText}>{getStatusText()}</Text>
      
      <Animated.View style={[styles.buttonContainer, { transform: [{ scale: pulseAnim }] }]}>
        <TouchableOpacity
          style={[
            styles.voiceButton,
            isListening && styles.listeningButton,
            isProcessing && styles.processingButton,
          ]}
          onPress={isListening ? onStopListening : onStartListening}
          disabled={isProcessing}
          activeOpacity={0.8}
        >
          <Text style={styles.micIcon}>
            {isProcessing ? '⏳' : isListening ? '🛑' : '🎤'}
          </Text>
        </TouchableOpacity>
      </Animated.View>

      <Text style={styles.buttonText}>{getButtonText()}</Text>
      
      {isListening && (
        <View style={styles.waveContainer}>
          <View style={[styles.wave, styles.wave1]} />
          <View style={[styles.wave, styles.wave2]} />
          <View style={[styles.wave, styles.wave3]} />
        </View>
      )}

      <View style={styles.tipsContainer}>
        <Text style={styles.tipsTitle}>
          {language === 'th' ? '💡 ตัวอย่างคำสั่ง:' : '💡 Example commands:'}
        </Text>
        <Text style={styles.tip}>
          {language === 'th' 
            ? '• "หาร้านอาหารใกล้ฉัน"'
            : '• "Find restaurants near me"'
          }
        </Text>
        <Text style={styles.tip}>
          {language === 'th' 
            ? '• "แนะนำสถานที่ท่องเที่ยวในกรุงเทพ"'
            : '• "Recommend tourist attractions in Bangkok"'
          }
        </Text>
        <Text style={styles.tip}>
          {language === 'th' 
            ? '• "วัดสวยๆ ที่ควรไป"'
            : '• "Beautiful temples to visit"'
          }
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'white',
  },
  statusText: {
    fontSize: 16,
    color: '#333',
    textAlign: 'center',
    marginBottom: 20,
    fontWeight: '500',
  },
  buttonContainer: {
    marginBottom: 16,
  },
  voiceButton: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#2196F3',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  listeningButton: {
    backgroundColor: '#f44336',
  },
  processingButton: {
    backgroundColor: '#FF9800',
  },
  micIcon: {
    fontSize: 36,
    color: 'white',
  },
  buttonText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  waveContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  wave: {
    width: 8,
    backgroundColor: '#2196F3',
    borderRadius: 4,
    marginHorizontal: 2,
  },
  wave1: {
    height: 20,
    animationDelay: '0s',
  },
  wave2: {
    height: 30,
    animationDelay: '0.1s',
  },
  wave3: {
    height: 25,
    animationDelay: '0.2s',
  },
  tipsContainer: {
    backgroundColor: '#f8f9fa',
    padding: 16,
    borderRadius: 12,
    width: '100%',
    marginTop: 10,
  },
  tipsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  tip: {
    fontSize: 13,
    color: '#666',
    marginBottom: 4,
    paddingLeft: 8,
  },
});

export default VoiceControls;