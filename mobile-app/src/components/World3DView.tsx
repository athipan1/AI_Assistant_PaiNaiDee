import React, { useEffect, useState, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Dimensions, Alert } from 'react-native';
import { GLView } from 'expo-gl';
import * as THREE from 'three';

interface World3DViewProps {
  apiBaseUrl: string;
  userId?: string;
  language?: 'en' | 'th';
  onLocationSelect?: (locationId: string) => void;
  onAIAction?: (action: string) => void;
}

interface LocationData {
  name: { en: string; th: string };
  description: { en: string; th: string };
  position: { x: number; y: number; z: number };
  category: string;
  rating: number;
  activities: string[];
}

interface AIAction {
  type: string;
  target?: string;
  position?: { x: number; y: number; z: number };
  timestamp: string;
}

const World3DView: React.FC<World3DViewProps> = ({
  apiBaseUrl,
  userId = 'mobile_user',
  language = 'en',
  onLocationSelect,
  onAIAction
}) => {
  const [scene, setScene] = useState<THREE.Scene | null>(null);
  const [camera, setCamera] = useState<THREE.PerspectiveCamera | null>(null);
  const [renderer, setRenderer] = useState<THREE.WebGLRenderer | null>(null);
  const [locations, setLocations] = useState<Record<string, LocationData>>({});
  const [aiCharacter, setAICharacter] = useState<THREE.Object3D | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [aiSpeech, setAISpeech] = useState<string>('');
  const [activeUsers, setActiveUsers] = useState<number>(1);
  
  const websocketRef = useRef<WebSocket | null>(null);
  const animationFrameRef = useRef<number>();

  // Tourist locations with Thai cultural sites
  const LOCATIONS = [
    { id: 'koh-samui', name: { en: 'Koh Samui', th: 'เกาะสมุย' }, emoji: '🏝️' },
    { id: 'temple', name: { en: 'Buddhist Temple', th: 'วัดพุทธ' }, emoji: '🏛️' },
    { id: 'market', name: { en: 'Floating Market', th: 'ตลาดน้ำ' }, emoji: '🛒' },
    { id: 'beach', name: { en: 'Tropical Beach', th: 'ชายหาด' }, emoji: '🏖️' },
    { id: 'restaurant', name: { en: 'Thai Restaurant', th: 'ร้านอาหาร' }, emoji: '🍜' }
  ];

  useEffect(() => {
    initializeWorld();
    fetchLocations();
    connectWebSocket();
    
    return () => {
      cleanup();
    };
  }, []);

  const initializeWorld = async () => {
    try {
      // This will be called when GLView is ready
      console.log('3D World initialization ready');
    } catch (error) {
      console.error('Error initializing 3D world:', error);
    }
  };

  const onContextCreate = async (gl: any) => {
    const { drawingBufferWidth: width, drawingBufferHeight: height } = gl;

    // Create THREE.js scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x87ceeb); // Sky blue

    // Create camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(0, 5, -10);

    // Create renderer
    const renderer = new THREE.WebGLRenderer({
      canvas: {
        width,
        height,
        style: {},
        addEventListener: () => {},
        removeEventListener: () => {},
        clientHeight: height,
        clientWidth: width,
        getContext: () => gl,
      } as any,
      context: gl,
    });
    renderer.setSize(width, height);

    // Add lighting
    const hemisphericLight = new THREE.HemisphericLight('hemisphericLight', new THREE.Vector3(0, 1, 0), scene);
    hemisphericLight.intensity = 0.7;

    const directionalLight = new THREE.DirectionalLight('directionalLight', new THREE.Vector3(-1, -1, -1), scene);
    directionalLight.intensity = 0.5;

    // Create ground
    const groundGeometry = new THREE.PlaneGeometry(50, 50);
    const groundMaterial = new THREE.MeshLambertMaterial({ color: 0x4a7c59 });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    scene.add(ground);

    // Create AI character (simple capsule for now)
    const aiGeometry = new THREE.CapsuleGeometry(0.5, 2);
    const aiMaterial = new THREE.MeshLambertMaterial({ 
      color: 0x4ecdc4,
      emissive: 0x001122
    });
    const aiChar = new THREE.Mesh(aiGeometry, aiMaterial);
    aiChar.position.set(0, 1, 0);
    scene.add(aiChar);

    // Create location markers
    await createLocationMarkers(scene);

    // Store references
    setScene(scene);
    setCamera(camera);
    setRenderer(renderer);
    setAICharacter(aiChar);

    // Start render loop
    const render = () => {
      animationFrameRef.current = requestAnimationFrame(render);
      
      // Simple floating animation for AI character
      if (aiChar) {
        aiChar.position.y = 1 + Math.sin(Date.now() * 0.002) * 0.2;
        aiChar.rotation.y += 0.01;
      }
      
      renderer.render(scene, camera);
      gl.endFrameEXP();
    };
    render();
  };

  const createLocationMarkers = async (scene: THREE.Scene) => {
    const locationPositions = [
      { x: 10, y: 0.75, z: 5 },   // koh-samui
      { x: -10, y: 0.75, z: 5 },  // temple
      { x: 0, y: 0.75, z: 15 },   // market
      { x: 15, y: 0.75, z: -5 },  // beach
      { x: -5, y: 0.75, z: -10 }  // restaurant
    ];

    const colors = [0x00a8ff, 0xffd700, 0xff6b6b, 0x4ecdc4, 0x45b7d1];

    LOCATIONS.forEach((location, index) => {
      const markerGeometry = new THREE.SphereGeometry(1, 16, 16);
      const markerMaterial = new THREE.MeshLambertMaterial({ 
        color: colors[index],
        emissive: colors[index],
        emissiveIntensity: 0.3
      });
      const marker = new THREE.Mesh(markerGeometry, markerMaterial);
      marker.position.copy(locationPositions[index]);
      marker.userData = { locationId: location.id };
      scene.add(marker);

      // Add floating animation
      const originalY = marker.position.y;
      const animate = () => {
        marker.position.y = originalY + Math.sin(Date.now() * 0.001 + index) * 0.3;
      };
      
      // Add to animation loop (simplified for mobile)
      setInterval(animate, 16);
    });
  };

  const fetchLocations = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/3d_world/locations`);
      const data = await response.json();
      if (data.status === 'success') {
        setLocations(data.locations);
      }
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const connectWebSocket = () => {
    try {
      const wsUrl = apiBaseUrl.replace('http', 'ws') + `/3d_world/ws/${userId}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('Connected to 3D world WebSocket');
        setIsConnected(true);
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      };
      
      ws.onclose = () => {
        console.log('Disconnected from 3D world WebSocket');
        setIsConnected(false);
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      websocketRef.current = ws;
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
    }
  };

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'ai_action':
        handleAIAction(message.data);
        break;
      case 'user_update':
        setActiveUsers(message.user_count);
        break;
      case 'chat':
        // Handle chat messages from other users
        console.log('Chat message:', message);
        break;
    }
  };

  const handleAIAction = (actionData: AIAction) => {
    console.log('AI Action:', actionData);
    
    if (actionData.type === 'navigate' && aiCharacter && actionData.position) {
      // Animate AI character to new position
      const targetPosition = new THREE.Vector3(
        actionData.position.x,
        actionData.position.y,
        actionData.position.z
      );
      
      // Simple animation to target position
      const startPosition = aiCharacter.position.clone();
      const duration = 2000; // 2 seconds
      const startTime = Date.now();
      
      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        aiCharacter.position.lerpVectors(startPosition, targetPosition, progress);
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };
      animate();
    }
    
    if (onAIAction) {
      onAIAction(actionData.type);
    }
  };

  const navigateAIToLocation = async (locationId: string) => {
    try {
      const response = await fetch(`${apiBaseUrl}/3d_world/ai/navigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'navigate',
          target_location: locationId,
          language: language
        })
      });
      
      const data = await response.json();
      if (data.status === 'success' && data.ai_response) {
        setAISpeech(data.ai_response.message);
        // Clear speech after 4 seconds
        setTimeout(() => setAISpeech(''), 4000);
      }
      
      if (onLocationSelect) {
        onLocationSelect(locationId);
      }
    } catch (error) {
      console.error('Error navigating AI:', error);
      Alert.alert('Error', 'Failed to navigate AI to location');
    }
  };

  const executeAIAction = async (actionType: string) => {
    try {
      const response = await fetch(`${apiBaseUrl}/3d_world/ai/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: actionType,
          language: language
        })
      });
      
      const data = await response.json();
      if (data.status === 'success' && data.response) {
        setAISpeech(data.response.message);
        setTimeout(() => setAISpeech(''), 4000);
      }
    } catch (error) {
      console.error('Error executing AI action:', error);
    }
  };

  const cleanup = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (websocketRef.current) {
      websocketRef.current.close();
    }
  };

  const { width } = Dimensions.get('window');

  return (
    <View style={styles.container}>
      {/* 3D World View */}
      <GLView 
        style={styles.glView} 
        onContextCreate={onContextCreate}
      />
      
      {/* Connection Status */}
      <View style={[styles.statusBar, { backgroundColor: isConnected ? '#4CAF50' : '#F44336' }]}>
        <Text style={styles.statusText}>
          {isConnected ? `🌐 Connected (${activeUsers} users)` : '🔴 Disconnected'}
        </Text>
      </View>
      
      {/* AI Speech Bubble */}
      {aiSpeech !== '' && (
        <View style={styles.speechBubble}>
          <Text style={styles.speechText}>{aiSpeech}</Text>
        </View>
      )}
      
      {/* Location Controls */}
      <View style={styles.locationControls}>
        <Text style={styles.controlTitle}>
          {language === 'th' ? '🏝️ สถานที่ท่องเที่ยว' : '🏝️ Tourist Locations'}
        </Text>
        <View style={styles.locationGrid}>
          {LOCATIONS.map((location) => (
            <TouchableOpacity
              key={location.id}
              style={styles.locationButton}
              onPress={() => navigateAIToLocation(location.id)}
            >
              <Text style={styles.locationEmoji}>{location.emoji}</Text>
              <Text style={styles.locationName}>
                {location.name[language]}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
      
      {/* AI Action Controls */}
      <View style={styles.actionControls}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => executeAIAction('greet')}
        >
          <Text style={styles.actionButtonText}>👋</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => executeAIAction('dance')}
        >
          <Text style={styles.actionButtonText}>💃</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  glView: {
    flex: 1,
  },
  statusBar: {
    position: 'absolute',
    top: 40,
    left: 20,
    right: 20,
    padding: 8,
    borderRadius: 20,
    alignItems: 'center',
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  speechBubble: {
    position: 'absolute',
    top: 80,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    padding: 15,
    borderRadius: 20,
    alignItems: 'center',
  },
  speechText: {
    color: '#333',
    fontSize: 14,
    textAlign: 'center',
  },
  locationControls: {
    position: 'absolute',
    bottom: 120,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    padding: 15,
    borderRadius: 15,
  },
  controlTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
  },
  locationGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  locationButton: {
    width: '18%',
    aspectRatio: 1,
    backgroundColor: 'rgba(255, 221, 89, 0.9)',
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 5,
  },
  locationEmoji: {
    fontSize: 16,
  },
  locationName: {
    fontSize: 8,
    color: '#333',
    textAlign: 'center',
    fontWeight: 'bold',
  },
  actionControls: {
    position: 'absolute',
    bottom: 40,
    left: '50%',
    marginLeft: -60,
    flexDirection: 'row',
    gap: 20,
  },
  actionButton: {
    width: 50,
    height: 50,
    backgroundColor: 'rgba(255, 221, 89, 0.9)',
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionButtonText: {
    fontSize: 24,
  },
});

export default World3DView;