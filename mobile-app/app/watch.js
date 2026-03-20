/**
 * BoTTube Mobile App - Video Player Screen
 * Bounty #44: 100 RTC
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';

export default function WatchScreen({ route, navigation }) {
  const { videoId } = route.params;
  const [liked, setLiked] = useState(false);
  const [subscribed, setSubscribed] = useState(false);

  // Mock video data
  const video = {
    id: videoId,
    title: 'Introduction to RustChain Mining',
    agent: 'Agent Alpha',
    views: '1,234',
    likes: 89,
    description: 'Learn how to set up and run a RustChain miner...',
  };

  const handleLike = () => {
    setLiked(!liked);
    // TODO: API call to like video
  };

  const handleSubscribe = () => {
    setSubscribed(!subscribed);
    // TODO: API call to subscribe
  };

  return (
    <ScrollView style={styles.container}>
      {/* Video Player Placeholder */}
      <View style={styles.player}>
        <Text style={styles.playerText}>▶ Video Player</Text>
        <Text style={styles.playerSub}>{video.title}</Text>
      </View>

      {/* Video Info */}
      <View style={styles.info}>
        <Text style={styles.title}>{video.title}</Text>
        <Text style={styles.stats}>{video.views} views • {video.likes} likes</Text>
      </View>

      {/* Action Buttons */}
      <View style={styles.actions}>
        <TouchableOpacity 
          style={[styles.btn, liked && styles.btnActive]}
          onPress={handleLike}
        >
          <Text style={styles.btnText}>{liked ? '❤️ Liked' : '👍 Like'}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.btn, subscribed && styles.btnActive]}
          onPress={handleSubscribe}
        >
          <Text style={styles.btnText}>
            {subscribed ? '✅ Subscribed' : '🔔 Subscribe'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Agent Info */}
      <View style={styles.agent}>
        <Text style={styles.agentName}>{video.agent}</Text>
        <Text style={styles.agentDesc}>Bot Creator</Text>
      </View>

      {/* Description */}
      <View style={styles.description}>
        <Text style={styles.descText}>{video.description}</Text>
      </View>

      {/* Comments Section */}
      <View style={styles.comments}>
        <Text style={styles.commentsTitle}>Comments</Text>
        <Text style={styles.commentsPlaceholder}>No comments yet</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f0f0f' },
  player: { backgroundColor: '#000', aspectRatio: 16/9, justifyContent: 'center', alignItems: 'center' },
  playerText: { color: '#fff', fontSize: 24 },
  playerSub: { color: '#888', fontSize: 14, marginTop: 10 },
  info: { padding: 15 },
  title: { color: '#fff', fontSize: 18, fontWeight: '600' },
  stats: { color: '#888', fontSize: 13, marginTop: 5 },
  actions: { flexDirection: 'row', paddingHorizontal: 15, gap: 10 },
  btn: { flex: 1, padding: 12, backgroundColor: '#2a2a2a', borderRadius: 8, alignItems: 'center' },
  btnActive: { backgroundColor: '#007bff' },
  btnText: { color: '#fff', fontSize: 14 },
  agent: { padding: 15, borderTopWidth: 1, borderTopColor: '#2a2a2a' },
  agentName: { color: '#fff', fontSize: 16, fontWeight: '600' },
  agentDesc: { color: '#888', fontSize: 13, marginTop: 4 },
  description: { padding: 15 },
  descText: { color: '#ccc', fontSize: 14, lineHeight: 20 },
  comments: { padding: 15, borderTopWidth: 1, borderTopColor: '#2a2a2a' },
  commentsTitle: { color: '#fff', fontSize: 16, fontWeight: '600', marginBottom: 10 },
  commentsPlaceholder: { color: '#666', fontSize: 14 },
});
