"""
BoTTube Recommendation Engine - AI-Powered Feed
Implements content-based filtering, collaborative filtering, and trending algorithms.
"""

import sqlite3
import math
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import re


class RecommendationEngine:
    """
    Comprehensive recommendation system for BoTTube.
    
    Features:
    - Content-based filtering (video titles, descriptions, tags)
    - Collaborative filtering ("users who watched X also watched Y")
    - Trending algorithm (time-weighted views, engagement rate)
    """
    
    def __init__(self, db_path: str = "bottube.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    # ==================== Content-Based Filtering ====================
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (title, description, tags)."""
        if not text:
            return []
        # Remove special characters and convert to lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())
        # Split into words and remove stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [w for w in text.split() if w not in stop_words and len(w) > 2]
        return words
    
    def calculate_content_similarity(self, video1_id: int, video2_id: int) -> float:
        """
        Calculate content similarity between two videos based on:
        - Title keywords
        - Description keywords
        - Tags overlap
        - Category match
        """
        cursor = self.conn.cursor()
        
        # Get video 1 data
        cursor.execute("""
            SELECT title, description, category, tags 
            FROM videos WHERE id = ?
        """, (video1_id,))
        v1 = cursor.fetchone()
        
        # Get video 2 data
        cursor.execute("""
            SELECT title, description, category, tags 
            FROM videos WHERE id = ?
        """, (video2_id,))
        v2 = cursor.fetchone()
        
        if not v1 or not v2:
            return 0.0
        
        # Extract keywords
        v1_keywords = set(self.extract_keywords(v1['title'] + ' ' + (v1['description'] or '')))
        v2_keywords = set(self.extract_keywords(v2['title'] + ' ' + (v2['description'] or '')))
        
        # Tag overlap
        v1_tags = set((v1['tags'] or '').split(',')) if v1['tags'] else set()
        v2_tags = set((v2['tags'] or '').split(',')) if v2['tags'] else set()
        
        # Calculate Jaccard similarity for keywords
        keyword_intersection = len(v1_keywords & v2_keywords)
        keyword_union = len(v1_keywords | v2_keywords)
        keyword_sim = keyword_intersection / keyword_union if keyword_union > 0 else 0
        
        # Tag similarity
        tag_intersection = len(v1_tags & v2_tags)
        tag_union = len(v1_tags | v2_tags)
        tag_sim = tag_intersection / tag_union if tag_union > 0 else 0
        
        # Category match (binary)
        category_sim = 1.0 if v1['category'] == v2['category'] else 0.0
        
        # Weighted combination
        similarity = (0.4 * keyword_sim) + (0.4 * tag_sim) + (0.2 * category_sim)
        return similarity
    
    def get_content_based_recommendations(self, video_id: int, limit: int = 10) -> List[Dict]:
        """
        Get content-based recommendations for a video.
        Returns videos with similar content (keywords, tags, category).
        """
        cursor = self.conn.cursor()
        
        # Get all other videos
        cursor.execute("""
            SELECT id, title, description, category, tags, views, created_at
            FROM videos WHERE id != ?
        """, (video_id,))
        
        all_videos = cursor.fetchall()
        similarities = []
        
        for video in all_videos:
            sim = self.calculate_content_similarity(video_id, video['id'])
            if sim > 0.1:  # Threshold for relevance
                similarities.append({
                    'video_id': video['id'],
                    'title': video['title'],
                    'similarity': sim,
                    'views': video['views'],
                    'category': video['category']
                })
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:limit]
    
    # ==================== Collaborative Filtering ====================
    
    def get_user_watch_history(self, user_id: int, limit: int = 50) -> List[int]:
        """Get user's watch history (video IDs)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT video_id FROM watch_history 
            WHERE user_id = ? 
            ORDER BY watched_at DESC 
            LIMIT ?
        """, (user_id, limit))
        return [row['video_id'] for row in cursor.fetchall()]
    
    def find_similar_users(self, user_id: int, limit: int = 10) -> List[Tuple[int, float]]:
        """
        Find users with similar watch history.
        Returns list of (user_id, similarity_score) tuples.
        """
        cursor = self.conn.cursor()
        
        # Get target user's watch history
        target_history = set(self.get_user_watch_history(user_id))
        if not target_history:
            return []
        
        # Get all other users who watched similar videos
        cursor.execute("""
            SELECT DISTINCT user_id FROM watch_history 
            WHERE video_id IN ({}) AND user_id != ?
        """.format(','.join('?' * len(target_history))), (*target_history, user_id))
        
        other_users = [row['user_id'] for row in cursor.fetchall()]
        user_similarities = []
        
        for other_user in other_users:
            other_history = set(self.get_user_watch_history(other_user))
            if not other_history:
                continue
            
            # Jaccard similarity
            intersection = len(target_history & other_history)
            union = len(target_history | other_history)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.1:
                user_similarities.append((other_user, similarity))
        
        user_similarities.sort(key=lambda x: x[1], reverse=True)
        return user_similarities[:limit]
    
    def get_collaborative_recommendations(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Get collaborative filtering recommendations.
        "Users who watched X also watched Y"
        """
        cursor = self.conn.cursor()
        
        # Get user's watch history
        watch_history = set(self.get_user_watch_history(user_id))
        if not watch_history:
            return []
        
        # Find videos watched by similar users
        video_scores = defaultdict(float)
        
        similar_users = self.find_similar_users(user_id)
        for similar_user, similarity in similar_users:
            their_history = self.get_user_watch_history(similar_user)
            for video_id in their_history:
                if video_id not in watch_history:
                    video_scores[video_id] += similarity
        
        # Get video details for top scored videos
        recommendations = []
        for video_id, score in sorted(video_scores.items(), key=lambda x: x[1], reverse=True)[:limit * 2]:
            cursor.execute("""
                SELECT id, title, views, category, created_at 
                FROM videos WHERE id = ?
            """, (video_id,))
            video = cursor.fetchone()
            if video:
                recommendations.append({
                    'video_id': video['id'],
                    'title': video['title'],
                    'score': score,
                    'views': video['views'],
                    'category': video['category'],
                    'reason': 'Users like you watched this'
                })
        
        return recommendations[:limit]
    
    # ==================== Trending Algorithm ====================
    
    def calculate_trending_score(self, video_id: int) -> float:
        """
        Calculate trending score based on:
        - Time-weighted view count
        - Engagement rate (likes + comments / views)
        - Velocity (recent views vs historical average)
        - New content boost
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT views, likes, comments, created_at 
            FROM videos WHERE id = ?
        """, (video_id,))
        video = cursor.fetchone()
        
        if not video:
            return 0.0
        
        views = video['views'] or 0
        likes = video['likes'] or 0
        comments = video['comments'] or 0
        created_at = datetime.fromisoformat(video['created_at']) if video['created_at'] else datetime.now()
        
        # Time decay factor (newer content gets boost)
        age_hours = (datetime.now() - created_at).total_seconds() / 3600
        time_decay = math.exp(-age_hours / 168)  # 1 week half-life
        
        # Engagement rate
        engagement_rate = (likes + comments * 2) / views if views > 0 else 0
        
        # Velocity (views in last 24h vs total)
        cursor.execute("""
            SELECT COUNT(*) as recent_views FROM view_events 
            WHERE video_id = ? AND viewed_at > datetime('now', '-1 day')
        """, (video_id,))
        recent_views = cursor.fetchone()['recent_views']
        velocity = recent_views / max(views, 1)
        
        # Combined trending score
        score = (
            0.3 * math.log1p(views) +  # Base popularity
            0.3 * engagement_rate * 100 +  # Engagement quality
            0.2 * velocity * 10 +  # Velocity boost
            0.2 * time_decay * 10  # Recency boost
        )
        
        return score
    
    def get_trending_videos(self, limit: int = 20, category: Optional[str] = None) -> List[Dict]:
        """
        Get trending videos sorted by trending score.
        Optionally filter by category.
        """
        cursor = self.conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT id, title, views, likes, comments, created_at, category
                FROM videos WHERE category = ?
                ORDER BY views DESC LIMIT ?
            """, (category, limit * 3))
        else:
            cursor.execute("""
                SELECT id, title, views, likes, comments, created_at, category
                FROM videos ORDER BY views DESC LIMIT ?
            """, (limit * 3,))
        
        videos = cursor.fetchall()
        trending = []
        
        for video in videos:
            score = self.calculate_trending_score(video['id'])
            trending.append({
                'video_id': video['id'],
                'title': video['title'],
                'trending_score': score,
                'views': video['views'],
                'likes': video['likes'],
                'comments': video['comments'],
                'category': video['category']
            })
        
        # Sort by trending score
        trending.sort(key=lambda x: x['trending_score'], reverse=True)
        return trending[:limit]
    
    # ==================== Personalized Feed ====================
    
    def get_personalized_feed(self, user_id: int, limit: int = 20) -> List[Dict]:
        """
        Get personalized "For You" feed combining:
        - Content-based recommendations (40%)
        - Collaborative filtering (40%)
        - Trending content (20%)
        """
        # Get content-based recommendations
        watch_history = self.get_user_watch_history(user_id)
        content_recs = []
        if watch_history:
            # Use most recent watched video as seed
            seed_video = watch_history[0]
            content_recs = self.get_content_based_recommendations(seed_video, limit)
        
        # Get collaborative recommendations
        collab_recs = self.get_collaborative_recommendations(user_id, limit)
        
        # Get trending videos
        trending = self.get_trending_videos(limit)
        
        # Combine with weights
        scored_videos = {}
        
        for i, rec in enumerate(content_recs):
            video_id = rec['video_id']
            score = rec['similarity'] * 0.4 * (1 - i / len(content_recs))  # Position decay
            scored_videos[video_id] = scored_videos.get(video_id, 0) + score
        
        for i, rec in enumerate(collab_recs):
            video_id = rec['video_id']
            score = rec['score'] * 0.4 * (1 - i / len(collab_recs))
            scored_videos[video_id] = scored_videos.get(video_id, 0) + score
        
        for i, video in enumerate(trending):
            video_id = video['video_id']
            score = video['trending_score'] * 0.2 * (1 - i / len(trending))
            scored_videos[video_id] = scored_videos.get(video_id, 0) + score
        
        # Sort and return
        sorted_videos = sorted(scored_videos.items(), key=lambda x: x[1], reverse=True)
        
        # Get full video details
        feed = []
        for video_id, score in sorted_videos[:limit]:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, title, description, category, tags, views, likes, comments, created_at
                FROM videos WHERE id = ?
            """, (video_id,))
            video = cursor.fetchone()
            if video:
                feed.append({
                    'video_id': video['id'],
                    'title': video['title'],
                    'description': video['description'],
                    'category': video['category'],
                    'views': video['views'],
                    'likes': video['likes'],
                    'comments': video['comments'],
                    'relevance_score': score
                })
        
        return feed
    
    # ==================== Similar Videos ====================
    
    def get_similar_videos(self, video_id: int, limit: int = 10) -> List[Dict]:
        """
        Get videos similar to the given video.
        Combines content similarity and co-watch patterns.
        """
        content_recs = self.get_content_based_recommendations(video_id, limit * 2)
        
        # Enhance with co-watch data
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT vh2.video_id, COUNT(*) as co_watch_count
            FROM watch_history vh1
            JOIN watch_history vh2 ON vh1.user_id = vh2.user_id AND vh1.video_id != vh2.video_id
            WHERE vh1.video_id = ?
            GROUP BY vh2.video_id
            ORDER BY co_watch_count DESC
            LIMIT ?
        """, (video_id, limit))
        
        co_watch_videos = cursor.fetchall()
        co_watch_ids = {row['video_id']: row['co_watch_count'] for row in co_watch_videos}
        
        # Boost content recommendations with co-watch data
        for rec in content_recs:
            if rec['video_id'] in co_watch_ids:
                rec['co_watch_boost'] = co_watch_ids[rec['video_id']]
                rec['similarity'] += co_watch_ids[rec['video_id']] * 0.1
        
        # Re-sort with boost
        content_recs.sort(key=lambda x: x['similarity'], reverse=True)
        return content_recs[:limit]
    
    # ==================== API Endpoints (Flask Example) ====================
    
    def create_flask_routes(self, app):
        """
        Create Flask API routes for the recommendation engine.
        
        Usage:
            from flask import Flask
            app = Flask(__name__)
            engine = RecommendationEngine()
            engine.create_flask_routes(app)
        """
        from flask import jsonify, request
        
        @app.route('/api/recommendations', methods=['GET'])
        def api_recommendations():
            """Get personalized recommendations for a user."""
            user_id = request.args.get('user_id', type=int)
            limit = request.args.get('limit', 20, type=int)
            
            if not user_id:
                return jsonify({'error': 'user_id required'}), 400
            
            recommendations = self.get_personalized_feed(user_id, limit)
            return jsonify({'recommendations': recommendations})
        
        @app.route('/api/trending', methods=['GET'])
        def api_trending():
            """Get trending videos."""
            limit = request.args.get('limit', 20, type=int)
            category = request.args.get('category', None)
            
            trending = self.get_trending_videos(limit, category)
            return jsonify({'trending': trending})
        
        @app.route('/api/similar', methods=['GET'])
        def api_similar():
            """Get videos similar to a given video."""
            video_id = request.args.get('video_id', type=int)
            limit = request.args.get('limit', 10, type=int)
            
            if not video_id:
                return jsonify({'error': 'video_id required'}), 400
            
            similar = self.get_similar_videos(video_id, limit)
            return jsonify({'similar': similar})


# ==================== Usage Example ====================

if __name__ == "__main__":
    # Example usage
    engine = RecommendationEngine("bottube.db")
    
    # Get personalized feed for user 1
    feed = engine.get_personalized_feed(user_id=1, limit=10)
    print(f"Personalized Feed: {len(feed)} videos")
    
    # Get trending videos
    trending = engine.get_trending_videos(limit=10)
    print(f"Trending: {len(trending)} videos")
    
    # Get similar videos
    similar = engine.get_similar_videos(video_id=1, limit=10)
    print(f"Similar: {len(similar)} videos")
    
    engine.close()
