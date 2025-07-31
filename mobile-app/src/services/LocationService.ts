import * as Location from 'expo-location';
import { Location as LocationType, Place } from '../types';

export class LocationService {
  async getCurrentLocation(): Promise<LocationType | null> {
    try {
      // Request location permissions
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        throw new Error('Location permission not granted');
      }

      // Get current position
      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });

      return {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        accuracy: location.coords.accuracy || undefined,
      };
    } catch (error) {
      console.error('Location Service Error:', error);
      return null;
    }
  }

  async getNearbyPlaces(location: LocationType, query: string = ''): Promise<Place[]> {
    try {
      // This would integrate with Google Places API or the backend
      // For now, returning mock data with real Bangkok locations
      
      const mockPlaces: Place[] = [
        {
          id: '1',
          name: 'วัดพระแก้ว',
          description: 'พระบรมมหาราชวัง วัดศักดิ์สิทธิ์ที่สำคัญที่สุดในประเทศไทย',
          location: { latitude: 13.7500, longitude: 100.4927 },
          distance: this.calculateDistance(location, { latitude: 13.7500, longitude: 100.4927 }),
          rating: 4.8,
          category: 'temple',
          photoUrl: 'https://example.com/wat-phra-kaew.jpg'
        },
        {
          id: '2',
          name: 'ตลาดจตุจักร',
          description: 'ตลาดนัดสุดสัปดาห์ที่ใหญ่ที่สุดในโลก',
          location: { latitude: 13.7998, longitude: 100.5501 },
          distance: this.calculateDistance(location, { latitude: 13.7998, longitude: 100.5501 }),
          rating: 4.5,
          category: 'market',
          photoUrl: 'https://example.com/chatuchak.jpg'
        },
        {
          id: '3',
          name: 'MBK Center',
          description: 'ห้างสรรพสินค้าชื่อดังใจกลางกรุงเทพ',
          location: { latitude: 13.7449, longitude: 100.5308 },
          distance: this.calculateDistance(location, { latitude: 13.7449, longitude: 100.5308 }),
          rating: 4.2,
          category: 'shopping',
          photoUrl: 'https://example.com/mbk.jpg'
        },
        {
          id: '4',
          name: 'เซ็นทรัลเวิลด์',
          description: 'ห้างสรรพสินค้าระดับโลกใจกลางกรุงเทพ',
          location: { latitude: 13.7472, longitude: 100.5398 },
          distance: this.calculateDistance(location, { latitude: 13.7472, longitude: 100.5398 }),
          rating: 4.6,
          category: 'shopping',
          photoUrl: 'https://example.com/centralworld.jpg'
        },
        {
          id: '5',
          name: 'ร้านต้มยำกุ้งป้าป้อม',
          description: 'ร้านอาหารไทยต้นตำรับรสชาติดั้งเดิม',
          location: { latitude: 13.7563, longitude: 100.5018 },
          distance: this.calculateDistance(location, { latitude: 13.7563, longitude: 100.5018 }),
          rating: 4.7,
          category: 'restaurant',
          photoUrl: 'https://example.com/restaurant.jpg'
        }
      ];

      if (query) {
        return mockPlaces.filter(place => 
          place.name.toLowerCase().includes(query.toLowerCase()) ||
          place.description.toLowerCase().includes(query.toLowerCase()) ||
          place.category.toLowerCase().includes(query.toLowerCase())
        );
      }

      return mockPlaces.sort((a, b) => (a.distance || 0) - (b.distance || 0));
    } catch (error) {
      console.error('Nearby Places Error:', error);
      return [];
    }
  }

  private calculateDistance(loc1: LocationType, loc2: LocationType): number {
    const R = 6371; // Earth's radius in kilometers
    const dLat = this.deg2rad(loc2.latitude - loc1.latitude);
    const dLon = this.deg2rad(loc2.longitude - loc1.longitude);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.deg2rad(loc1.latitude)) *
        Math.cos(this.deg2rad(loc2.latitude)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  private deg2rad(deg: number): number {
    return deg * (Math.PI / 180);
  }

  async watchLocation(callback: (location: LocationType) => void): Promise<void> {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        throw new Error('Location permission not granted');
      }

      await Location.watchPositionAsync(
        {
          accuracy: Location.Accuracy.High,
          timeInterval: 5000, // Update every 5 seconds
          distanceInterval: 10, // Update every 10 meters
        },
        (location) => {
          callback({
            latitude: location.coords.latitude,
            longitude: location.coords.longitude,
            accuracy: location.coords.accuracy || undefined,
          });
        }
      );
    } catch (error) {
      console.error('Location Watch Error:', error);
    }
  }
}