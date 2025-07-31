import React, { useRef, useEffect, useState } from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { GLView, ExpoWebGLRenderingContext } from 'expo-gl';
import * as THREE from 'three';
import ExpoTHREE from 'expo-three';

interface AR3DViewProps {
  emotion?: string;
  gesture?: string;
  onModelLoad?: () => void;
}

const AR3DView: React.FC<AR3DViewProps> = ({ emotion, gesture, onModelLoad }) => {
  const glRef = useRef<ExpoWebGLRenderingContext | null>(null);
  const [scene, setScene] = useState<THREE.Scene | null>(null);
  const [camera, setCamera] = useState<THREE.PerspectiveCamera | null>(null);
  const [renderer, setRenderer] = useState<THREE.WebGLRenderer | null>(null);
  const [model, setModel] = useState<THREE.Object3D | null>(null);

  const onContextCreate = async (gl: ExpoWebGLRenderingContext) => {
    glRef.current = gl;
    const { drawingBufferWidth: width, drawingBufferHeight: height } = gl;

    // Create THREE.js scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);

    // Create camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(0, 0, 5);

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
    renderer.setClearColor(0x000000, 0);

    // Add lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);

    // Add a simple 3D model (cube with Thai colors)
    const geometry = new THREE.BoxGeometry(2, 2, 2);
    const materials = [
      new THREE.MeshLambertMaterial({ color: 0xff0000 }), // Red
      new THREE.MeshLambertMaterial({ color: 0xffffff }), // White  
      new THREE.MeshLambertMaterial({ color: 0x0000ff }), // Blue
      new THREE.MeshLambertMaterial({ color: 0xff0000 }), // Red
      new THREE.MeshLambertMaterial({ color: 0xffffff }), // White
      new THREE.MeshLambertMaterial({ color: 0x0000ff }), // Blue
    ];
    
    const cube = new THREE.Mesh(geometry, materials);
    scene.add(cube);
    setModel(cube);

    // Add particles for ambient effect
    const particleGeometry = new THREE.BufferGeometry();
    const particleCount = 100;
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i++) {
      positions[i] = (Math.random() - 0.5) * 10;
    }

    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMaterial = new THREE.PointsMaterial({ color: 0x888888, size: 0.05 });
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    setScene(scene);
    setCamera(camera);
    setRenderer(renderer);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      
      // Rotate the cube
      if (cube) {
        cube.rotation.x += 0.01;
        cube.rotation.y += 0.01;
        
        // Apply emotion-based animations
        if (emotion === 'excited') {
          cube.rotation.y += 0.02; // Faster rotation
          cube.scale.setScalar(1 + 0.1 * Math.sin(Date.now() * 0.01)); // Pulsing
        } else if (emotion === 'calm') {
          cube.rotation.y += 0.005; // Slower rotation
        }
      }

      // Animate particles
      if (particles) {
        particles.rotation.y += 0.001;
      }

      renderer.render(scene, camera);
      gl.endFrameEXP();
    };

    animate();
    onModelLoad?.();
  };

  useEffect(() => {
    if (model && emotion) {
      // Update model based on emotion
      switch (emotion) {
        case 'excited':
          model.material = new THREE.MeshLambertMaterial({ color: 0x00ff00 }); // Green
          break;
        case 'happy':
          model.material = new THREE.MeshLambertMaterial({ color: 0xffff00 }); // Yellow
          break;
        case 'worried':
          model.material = new THREE.MeshLambertMaterial({ color: 0xff8800 }); // Orange
          break;
        default:
          model.material = new THREE.MeshLambertMaterial({ color: 0x888888 }); // Gray
      }
    }
  }, [emotion, model]);

  return (
    <View style={styles.container}>
      <GLView
        style={styles.glView}
        onContextCreate={onContextCreate}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'black',
  },
  glView: {
    flex: 1,
  },
});

export default AR3DView;