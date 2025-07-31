import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, FlatList, Image } from 'react-native';
import { Place } from '../types';

interface PlaceListProps {
  places: Place[];
  onPlaceSelect: (place: Place) => void;
  language: 'th' | 'en';
}

const PlaceList: React.FC<PlaceListProps> = ({ places, onPlaceSelect, language }) => {
  const renderPlace = ({ item }: { item: Place }) => (
    <TouchableOpacity
      style={styles.placeItem}
      onPress={() => onPlaceSelect(item)}
    >
      <View style={styles.placeContent}>
        <View style={styles.placeInfo}>
          <Text style={styles.placeName}>{item.name}</Text>
          <Text style={styles.placeDescription} numberOfLines={2}>
            {item.description}
          </Text>
          <View style={styles.placeDetails}>
            <Text style={styles.placeDistance}>
              {item.distance ? `${item.distance.toFixed(1)} km` : ''}
            </Text>
            {item.rating && (
              <Text style={styles.placeRating}>
                ⭐ {item.rating}
              </Text>
            )}
            <Text style={styles.placeCategory}>
              {getCategoryName(item.category, language)}
            </Text>
          </View>
        </View>
        <View style={styles.placeThumbnail}>
          <Text style={styles.categoryEmoji}>
            {getCategoryEmoji(item.category)}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  if (places.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>
          {language === 'th' 
            ? 'ไม่พบสถานที่ที่เกี่ยวข้อง'
            : 'No places found'
          }
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>
        {language === 'th' 
          ? `พบสถานที่ ${places.length} แห่ง`
          : `Found ${places.length} places`
        }
      </Text>
      <FlatList
        data={places}
        renderItem={renderPlace}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.listContainer}
      />
    </View>
  );
};

const getCategoryEmoji = (category: string): string => {
  const emojiMap: { [key: string]: string } = {
    temple: '🏛️',
    restaurant: '🍽️',
    hotel: '🏨',
    shopping: '🛍️',
    market: '🛒',
    attraction: '🎯',
    park: '🌳',
    museum: '🏛️',
    hospital: '🏥',
    school: '🏫',
  };
  return emojiMap[category] || '📍';
};

const getCategoryName = (category: string, language: 'th' | 'en'): string => {
  const categoryNames: { [key: string]: { th: string; en: string } } = {
    temple: { th: 'วัด', en: 'Temple' },
    restaurant: { th: 'ร้านอาหาร', en: 'Restaurant' },
    hotel: { th: 'โรงแรม', en: 'Hotel' },
    shopping: { th: 'ห้างสรรพสินค้า', en: 'Shopping' },
    market: { th: 'ตลาด', en: 'Market' },
    attraction: { th: 'สถานที่ท่องเที่ยว', en: 'Attraction' },
    park: { th: 'สวนสาธารณะ', en: 'Park' },
    museum: { th: 'พิพิธภัณฑ์', en: 'Museum' },
    hospital: { th: 'โรงพยาบาล', en: 'Hospital' },
    school: { th: 'โรงเรียน', en: 'School' },
  };
  return categoryNames[category]?.[language] || category;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    padding: 16,
    color: '#333',
    backgroundColor: 'white',
  },
  listContainer: {
    padding: 8,
  },
  placeItem: {
    backgroundColor: 'white',
    marginVertical: 4,
    marginHorizontal: 8,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  placeContent: {
    flexDirection: 'row',
    padding: 16,
  },
  placeInfo: {
    flex: 1,
    marginRight: 12,
  },
  placeName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  placeDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    lineHeight: 20,
  },
  placeDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  placeDistance: {
    fontSize: 12,
    color: '#2196F3',
    marginRight: 12,
    fontWeight: '500',
  },
  placeRating: {
    fontSize: 12,
    color: '#FF9800',
    marginRight: 12,
    fontWeight: '500',
  },
  placeCategory: {
    fontSize: 12,
    color: '#4CAF50',
    backgroundColor: '#E8F5E8',
    paddingVertical: 2,
    paddingHorizontal: 6,
    borderRadius: 10,
    fontWeight: '500',
  },
  placeThumbnail: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#f0f0f0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  categoryEmoji: {
    fontSize: 24,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
});

export default PlaceList;