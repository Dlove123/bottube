"""
Tests for BoTTube Discoverability Engine
"""

import unittest
import sqlite3
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discoverability_engine import DiscoverabilityEngine


class TestDiscoverabilityEngine(unittest.TestCase):
    """Test cases for DiscoverabilityEngine."""
    
    def setUp(self):
        """Set up test database."""
        self.test_db = ":memory:"
        self.engine = DiscoverabilityEngine(self.test_db)
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
        
        # Agents table
        cursor.execute("""
            CREATE TABLE agents (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                capabilities TEXT,
                subscriber_count INTEGER DEFAULT 0,
                video_count INTEGER DEFAULT 0,
                last_active TEXT,
                created_at TEXT
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
            (6, "Python Web Development", "Build web apps with Python", "Education", "python,web,backend", 600, 35, 7, "2026-03-06T10:00:00"),
        ]
        
        cursor.executemany("""
            INSERT INTO videos (id, title, description, category, tags, views, likes, comments, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, videos)
        
        # Insert watch history for user 1
        watch_history = [
            (1, 1, 1, "2026-03-15T10:00:00"),
            (2, 1, 2, "2026-03-15T11:00:00"),
            (3, 1, 6, "2026-03-15T12:00:00"),
        ]
        
        cursor.executemany("""
            INSERT INTO watch_history (id, user_id, video_id, watched_at)
            VALUES (?, ?, ?, ?)
        """, watch_history)
        
        # Insert view events (recent)
        now = datetime.now()
        view_events = [
            (1, 1, (now - timedelta(hours=1)).isoformat()),
            (2, 1, (now - timedelta(hours=2)).isoformat()),
            (3, 4, (now - timedelta(hours=1)).isoformat()),
            (4, 4, (now - timedelta(hours=2)).isoformat()),
            (5, 4, (now - timedelta(hours=3)).isoformat()),
        ]
        
        cursor.executemany("""
            INSERT INTO view_events (id, video_id, viewed_at)
            VALUES (?, ?, ?)
        """, view_events)
        
        # Insert test agents
        agents = [
            (1, "CodeBot", "Programming tutorial bot", "python,javascript,education", 1000, 50, now.isoformat(), "2026-01-01T00:00:00"),
            (2, "FunnyBot", "Entertainment and comedy", "comedy,entertainment,funny", 5000, 200, now.isoformat(), "2026-01-02T00:00:00"),
            (3, "PetBot", "Pet care and training", "pets,dogs,cats,training", 500, 30, (now - timedelta(days=1)).isoformat(), "2026-01-03T00:00:00"),
        ]
        
        cursor.executemany("""
            INSERT INTO agents (id, name, description, capabilities, subscriber_count, video_count, last_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, agents)
        
        self.engine.conn.commit()
    
    # ==================== Search Tests ====================
    
    def test_search_videos(self):
        """Test full-text search."""
        results = self.engine.search_videos("python")
        
        self.assertGreater(len(results), 0)
        self.assertTrue(all('python' in r['title'].lower() or 'python' in str(r['tags']).lower() for r in results))
    
    def test_search_videos_no_results(self):
        """Test search with no results."""
        results = self.engine.search_videos("nonexistent_xyz123")
        self.assertEqual(len(results), 0)
    
    def test_search_with_limit(self):
        """Test search with limit."""
        results = self.engine.search_videos("python", limit=2)
        self.assertLessEqual(len(results), 2)
    
    # ==================== Category Tests ====================
    
    def test_get_categories(self):
        """Test getting categories."""
        categories = self.engine.get_categories()
        
        self.assertGreater(len(categories), 0)
        self.assertTrue(all('name' in c and 'video_count' in c for c in categories))
    
    def test_filter_by_category(self):
        """Test filtering by category."""
        videos = self.engine.filter_by_category("Education", limit=10)
        
        self.assertGreater(len(videos), 0)
        self.assertTrue(all(v['category'] == 'Education' for v in videos))
    
    def test_filter_by_category_empty(self):
        """Test filtering by non-existent category."""
        videos = self.engine.filter_by_category("NonExistent")
        self.assertEqual(len(videos), 0)
    
    # ==================== Tag Tests ====================
    
    def test_get_all_tags(self):
        """Test getting all tags."""
        tags = self.engine.get_all_tags()
        
        self.assertGreater(len(tags), 0)
        self.assertTrue(all('name' in t and 'count' in t for t in tags))
    
    def test_filter_by_tag(self):
        """Test filtering by tag."""
        videos = self.engine.filter_by_tag("python", limit=10)
        
        self.assertGreater(len(videos), 0)
        # All results should have python tag
        for v in videos:
            self.assertTrue(any('python' in tag.lower() for tag in v['tags']))
    
    # ==================== Trending Tests ====================
    
    def test_get_trending_videos(self):
        """Test getting trending videos."""
        trending = self.engine.get_trending_videos('24h', limit=10)
        
        self.assertGreater(len(trending), 0)
        self.assertTrue(all('trending_score' in v for v in trending))
    
    def test_get_trending_videos_timeframe(self):
        """Test trending with different timeframes."""
        for timeframe in ['1h', '24h', '7d', '30d']:
            trending = self.engine.get_trending_videos(timeframe, limit=10)
            self.assertIsInstance(trending, list)
    
    # ==================== For You Feed Tests ====================
    
    def test_get_for_you_feed(self):
        """Test personalized feed."""
        feed = self.engine.get_for_you_feed(1, limit=10)
        
        self.assertGreater(len(feed), 0)
        self.assertTrue(all('reason' in v for v in feed))
    
    def test_get_for_you_feed_new_user(self):
        """Test feed for new user with no history."""
        feed = self.engine.get_for_you_feed(999, limit=10)
        
        # Should still return popular videos
        self.assertGreater(len(feed), 0)
    
    # ==================== Agent Directory Tests ====================
    
    def test_get_agents(self):
        """Test getting agents."""
        agents = self.engine.get_agents(limit=10)
        
        self.assertGreater(len(agents), 0)
        self.assertTrue(all('name' in a and 'subscribers' in a for a in agents))
    
    def test_get_agents_filter_by_capability(self):
        """Test filtering agents by capability."""
        agents = self.engine.get_agents(filter_by='python', limit=10)
        
        self.assertGreater(len(agents), 0)
    
    def test_get_agents_sort_by(self):
        """Test sorting agents."""
        for sort_by in ['subscribers', 'videos', 'activity']:
            agents = self.engine.get_agents(sort_by=sort_by, limit=10)
            self.assertIsInstance(agents, list)


class TestDiscoverabilityEngineFTS(unittest.TestCase):
    """Test FTS setup and functionality."""
    
    def setUp(self):
        """Set up test database."""
        self.test_db = ":memory:"
        self.engine = DiscoverabilityEngine(self.test_db)
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
        
        self.engine.conn.commit()
    
    def test_setup_fts(self):
        """Test FTS setup."""
        # Should not raise exception
        self.engine.setup_fts()
        
        # Check FTS table exists
        cursor = self.engine.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='videos_fts'
        """)
        result = cursor.fetchone()
        self.assertIsNotNone(result)
    
    def test_search_after_fts_setup(self):
        """Test search after FTS setup."""
        self.engine.setup_fts()
        
        # Insert test video
        cursor = self.engine.conn.cursor()
        cursor.execute("""
            INSERT INTO videos (title, description, tags, views)
            VALUES ('Python Tutorial', 'Learn Python', 'python,programming', 100)
        """)
        self.engine.conn.commit()
        
        # Search should work
        results = self.engine.search_videos("python")
        self.assertGreater(len(results), 0)


if __name__ == "__main__":
    unittest.main()
