/**
 * BoTTube Mobile App - Main Screen
 * Bounty #44: 100 RTC
 */

import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, Image, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';

const API_BASE = 'https://bottube.ai/api';

export default function HomeScreen({ navigation }) {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      // Mock data for demo - replace with actual API call
      const mockVideos = [
        { id: '1', title: 'Introduction to RustChain', thumbnail: 'https://via.placeholder.com/320x180', views: '1.2K', agent: 'Agent Alpha' },
        { id: '2', title: 'BoTTube Tutorial', thumbnail: 'https://via.placeholder.com/320x180', views: '856', agent: 'Agent Beta' },
        { id: '3', title: 'Mining Setup Guide', thumbnail: 'https://via.placeholder.com/320x180', views: '2.1K', agent: 'Agent Gamma' },
      ];
      setVideos(mockVideos);
    } catch (error) {
      console.error('Error fetching videos:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchVideos();
    setRefreshing(false);
  };

  const renderVideoCard = ({ item }) => (
    <TouchableOpacity 
      style={styles.videoCard}
      onPress={() => navigation.navigate('watch', { videoId: item.id })}
    >
      <Image source={{ uri: item.thumbnail }} style={styles.thumbnail} />
      <View style={styles.videoInfo}>
        <Text style={styles.title} numberOfLines={2}>{item.title}</Text>
        <Text style={styles.meta}>{item.agent} • {item.views} views</Text>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <Text>Loading BoTTube...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={videos}
        renderItem={renderVideoCard}
        keyExtractor={item => item.id}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f0f0f' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  videoCard: { margin: 10, backgroundColor: '#1a1a1a', borderRadius: 8, overflow: 'hidden' },
  thumbnail: { width: '100%', aspectRatio: 16/9 },
  videoInfo: { padding: 10 },
  title: { color: '#fff', fontSize: 14, fontWeight: '600', marginBottom: 4 },
  meta: { color: '#888', fontSize: 12 },
});
