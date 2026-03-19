"""
Tests for BoTTube Recommendation Engine
"""

import unittest
import sqlite3
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recommendation_engine import RecommendationEngine


class TestRecommendationEngine(unittest.TestCase):
    """Test cases for RecommendationEngine."""
    
    def setUp(self):
        """Set up test database."""
        self.test_db = ":memory:"
        self.engine = RecommendationEngine(self.test_db)
        self._create_test_schema()
        self._seed_test_data()
    
    def tearDown(self):
        """Clean up test database."""
        self.engine.close()
    
    def _create_test_schema(self):
        """Create test database schema."""
        cursor = self.engine.conn.cursor()
        
        # Videos table
        cursor.execute("""
            CREATE TABLE videos (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                tags TEXT,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        
        # Watch history table
        cursor.execute("""
            CREATE TABLE watch_history (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                video_id INTEGER NOT NULL,
                watched_at TEXT
            )
        """)
        
        # View events table
        cursor.execute("""
            CREATE TABLE view_events (
                id INTEGER PRIMARY KEY,
                video_id INTEGER NOT NULL,
                viewed_at TEXT
            )
        """)
        
        self.engine.conn.commit()
    
    def _seed_test_data(self):
        """Seed test database with sample data."""
        cursor = self.engine.conn.cursor()
        
        # Insert test videos
        videos = [
            (1, "Python Tutorial for Beginners", "Learn Python programming from scratch", "Education", "python,programming,beginners", 1000, 50, 10, "2026-03-01T10:00:00"),
            (2, "Advanced Python Tips", "Advanced Python programming techniques", "Education", "python,programming,advanced", 500, 30, 5, "2026-03-05T10:00:00"),
            (3, "JavaScript Basics", "Introduction to JavaScript", "Education", "javascript,programming,web", 800, 40, 8, "2026-03-02T10:00:00"),
            (4, "Funny Cat Compilation", "Hilarious cat videos", "Entertainment", "cats,funny,animals", 5000, 200, 50, "2026-03-10T10:00:00"),
            (5, "Dog Training Tips", "How to train your dog", "Pets", "dogs,training,pets", 300, 20, 3, "2026-03-08T10:00:00"),
        ]
        
        cursor.executemany("""
            INSERT INTO videos (id, title, description, category, tags, views, likes, comments, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, videos)
        
        # Insert watch history
        watch_history = [
            (1, 1, 1, "2026-03-15T10:00:00"),
            (2, 1, 2, "2026-03-15T11:00:00"),
            (3, 1, 3, "2026-03-15T12:00:00"),
            (4, 2, 1, "2026-03-14T10:00:00"),
            (5, 2, 2, "2026-03-14T11:00:00"),
            (6, 2, 4, "2026-03-14T12:00:00"),
        ]
        
        cursor.executemany("""
            INSERT INTO watch_history (id, user_id, video_id, watched_at)
            VALUES (?, ?, ?, ?)
        """, watch_history)
        
        # Insert view events
        now = datetime.now()
        view_events = [
            (1, 1, (now - timedelta(hours=1)).isoformat()),
            (2, 1, (now - timedelta(hours=2)).isoformat()),
            (3, 1, (now - timedelta(hours=3)).isoformat()),
            (4, 4, (now - timedelta(hours=1)).isoformat()),
            (5, 4, (now - timedelta(hours=2)).isoformat()),
        ]
        
        cursor.executemany("""
            INSERT INTO view_events (id, video_id, viewed_at)
            VALUES (?, ?, ?)
        """, view_events)
        
        self.engine.conn.commit()
    
    # ==================== Content-Based Filtering Tests ====================
    
    def test_extract_keywords(self):
        """Test keyword extraction from text."""
        text = "Learn Python programming from scratch"
        keywords = self.engine.extract_keywords(text)
        
        self.assertIn("python", keywords)
        self.assertIn("programming", keywords)
        self.assertNotIn("the", keywords)
        self.assertNotIn("from", keywords)
    
    def test_extract_keywords_empty(self):
        """Test keyword extraction with empty text."""
        keywords = self.engine.extract_keywords("")
        self.assertEqual(keywords, [])
    
    def test_calculate_content_similarity_same_category(self):
        """Test content similarity between videos in same category."""
        similarity = self.engine.calculate_content_similarity(1, 2)
        self.assertGreater(similarity, 0.3)  # Should have high similarity
    
    def test_calculate_content_similarity_different_category(self):
        """Test content similarity between videos in different categories."""
        similarity = self.engine.calculate_content_similarity(1, 4)
        self.assertLess(similarity, 0.3)  # Should have low similarity
    
    def test_get_content_based_recommendations(self):
        """Test content-based recommendations."""
        recommendations = self.engine.get_content_based_recommendations(1, limit=5)
        
        self.assertLessEqual(len(recommendations), 5)
        self.assertTrue(all('video_id' in rec for rec in recommendations))
        self.assertTrue(all('similarity' in rec for rec in recommendations))
    
    # ==================== Collaborative Filtering Tests ====================
    
    def test_get_user_watch_history(self):
        """Test getting user watch history."""
        history = self.engine.get_user_watch_history(1, limit=50)
        
        self.assertEqual(len(history), 3)
        self.assertIn(1, history)
        self.assertIn(2, history)
        self.assertIn(3, history)
    
    def test_find_similar_users(self):
        """Test finding similar users."""
        similar_users = self.engine.find_similar_users(1, limit=10)
        
        self.assertGreater(len(similar_users), 0)
        # User 2 should be similar (both watched videos 1 and 2)
        user_ids = [u[0] for u in similar_users]
        self.assertIn(2, user_ids)
    
    def test_get_collaborative_recommendations(self):
        """Test collaborative filtering recommendations."""
        recommendations = self.engine.get_collaborative_recommendations(1, limit=5)
        
        self.assertGreater(len(recommendations), 0)
        self.assertTrue(all('video_id' in rec for rec in recommendations))
        self.assertTrue(all('score' in rec for rec in recommendations))
    
    # ==================== Trending Algorithm Tests ====================
    
    def test_calculate_trending_score(self):
        """Test trending score calculation."""
        score = self.engine.calculate_trending_score(1)
        self.assertGreater(score, 0)
    
    def test_calculate_trending_score_nonexistent(self):
        """Test trending score for non-existent video."""
        score = self.engine.calculate_trending_score(999)
        self.assertEqual(score, 0.0)
    
    def test_get_trending_videos(self):
        """Test getting trending videos."""
        trending = self.engine.get_trending_videos(limit=10)
        
        self.assertGreater(len(trending), 0)
        self.assertLessEqual(len(trending), 10)
        self.assertTrue(all('trending_score' in v for v in trending))
    
    def test_get_trending_videos_by_category(self):
        """Test getting trending videos filtered by category."""
        trending = self.engine.get_trending_videos(limit=10, category="Education")
        
        self.assertGreater(len(trending), 0)
        self.assertTrue(all(v['category'] == 'Education' for v in trending))
    
    # ==================== Personalized Feed Tests ====================
    
    def test_get_personalized_feed(self):
        """Test personalized feed generation."""
        feed = self.engine.get_personalized_feed(1, limit=10)
        
        self.assertGreater(len(feed), 0)
        self.assertLessEqual(len(feed), 10)
        self.assertTrue(all('relevance_score' in v for v in feed))
    
    def test_get_personalized_feed_new_user(self):
        """Test personalized feed for new user with no history."""
        feed = self.engine.get_personalized_feed(999, limit=10)
        
        # Should still return trending videos
        self.assertGreater(len(feed), 0)
    
    # ==================== Similar Videos Tests ====================
    
    def test_get_similar_videos(self):
        """Test similar videos retrieval."""
        similar = self.engine.get_similar_videos(1, limit=5)
        
        self.assertGreater(len(similar), 0)
        self.assertLessEqual(len(similar), 5)
        self.assertTrue(all('similarity' in v for v in similar))


class TestRecommendationEngineEdgeCases(unittest.TestCase):
    """Edge case tests for RecommendationEngine."""
    
    def setUp(self):
        """Set up empty test database."""
        self.test_db = ":memory:"
        self.engine = RecommendationEngine(self.test_db)
        self._create_test_schema()
    
    def tearDown(self):
        """Clean up test database."""
        self.engine.close()
    
    def _create_test_schema(self):
        """Create minimal test database schema."""
        cursor = self.engine.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE videos (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                tags TEXT,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE watch_history (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                video_id INTEGER NOT NULL,
                watched_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE view_events (
                id INTEGER PRIMARY KEY,
                video_id INTEGER NOT NULL,
                viewed_at TEXT
            )
        """)
        
        self.engine.conn.commit()
    
    def test_empty_database_content_recommendations(self):
        """Test content recommendations with empty database."""
        recommendations = self.engine.get_content_based_recommendations(1, limit=10)
        self.assertEqual(recommendations, [])
    
    def test_empty_database_trending(self):
        """Test trending videos with empty database."""
        trending = self.engine.get_trending_videos(limit=10)
        self.assertEqual(trending, [])
    
    def test_empty_database_personalized_feed(self):
        """Test personalized feed with empty database."""
        feed = self.engine.get_personalized_feed(1, limit=10)
        self.assertEqual(feed, [])
    
    def test_nonexistent_video_similarity(self):
        """Test similarity with non-existent video."""
        similarity = self.engine.calculate_content_similarity(1, 999)
        self.assertEqual(similarity, 0.0)


if __name__ == "__main__":
    unittest.main()
