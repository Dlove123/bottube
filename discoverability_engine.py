"""
BoTTube Discoverability Engine
Implements search, filters, categories, tags, and trending features.
"""

import sqlite3
import re
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta


class DiscoverabilityEngine:
    """
    Video and agent discoverability system for BoTTube.
    
    Features:
    - Full-text search (titles, descriptions, tags)
    - Category filters
    - Tag system
    - Trending page
    - "For You" feed
    - Agent directory
    """
    
    def __init__(self, db_path: str = "bottube.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    # ==================== Full-Text Search ====================
    
    def setup_fts(self):
        """Setup FTS5 virtual table for full-text search."""
        cursor = self.conn.cursor()
        
        # Create FTS5 virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS videos_fts USING fts5(
                title,
                description,
                tags,
                content='videos',
                content_rowid='id'
            )
        """)
        
        # Create triggers to keep FTS index in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS videos_ai AFTER INSERT ON videos BEGIN
                INSERT INTO videos_fts(rowid, title, description, tags)
                VALUES (new.id, new.title, new.description, new.tags);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS videos_ad AFTER DELETE ON videos BEGIN
                INSERT INTO videos_fts(videos_fts, rowid, title, description, tags)
                VALUES('delete', old.id, old.title, old.description, old.tags);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS videos_au AFTER UPDATE ON videos BEGIN
                INSERT INTO videos_fts(videos_fts, rowid, title, description, tags)
                VALUES('delete', old.id, old.title, old.description, old.tags);
                INSERT INTO videos_fts(rowid, title, description, tags)
                VALUES (new.id, new.title, new.description, new.tags);
            END
        """)
        
        # Rebuild index from existing data
        cursor.execute("""
            INSERT OR REPLACE INTO videos_fts(rowid, title, description, tags)
            SELECT id, title, description, tags FROM videos
        """)
        
        self.conn.commit()
    
    def search_videos(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Full-text search across video titles, descriptions, and tags.
        
        Args:
            query: Search query string
            limit: Maximum number of results
        
        Returns:
            List of matching videos with relevance scores
        """
        cursor = self.conn.cursor()
        
        # Use FTS5 for full-text search
        try:
            cursor.execute("""
                SELECT v.id, v.title, v.description, v.category, v.tags,
                       v.views, v.likes, v.comments, v.created_at,
                       bm25(videos_fts) as relevance
                FROM videos_fts
                JOIN videos v ON videos_fts.rowid = v.id
                WHERE videos_fts MATCH ?
                ORDER BY relevance
                LIMIT ?
            """, (query, limit))
        except sqlite3.OperationalError:
            # Fallback to LIKE search if FTS not available
            search_pattern = f"%{query}%"
            cursor.execute("""
                SELECT id, title, description, category, tags,
                       views, likes, comments, created_at,
                       0 as relevance
                FROM videos
                WHERE title LIKE ? OR description LIKE ? OR tags LIKE ?
                ORDER BY views DESC
                LIMIT ?
            """, (search_pattern, search_pattern, search_pattern, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'video_id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'category': row['category'],
                'tags': row['tags'].split(',') if row['tags'] else [],
                'views': row['views'],
                'likes': row['likes'],
                'comments': row['comments'],
                'relevance_score': -row['relevance'] if row['relevance'] else 0
            })
        
        return results
    
    # ==================== Category System ====================
    
    def get_categories(self) -> List[Dict]:
        """Get all categories with video counts."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT category, COUNT(*) as video_count,
                   SUM(views) as total_views
            FROM videos
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY video_count DESC
        """)
        
        return [
            {
                'name': row['category'],
                'video_count': row['video_count'],
                'total_views': row['total_views']
            }
            for row in cursor.fetchall()
        ]
    
    def filter_by_category(self, category: str, limit: int = 20) -> List[Dict]:
        """Get videos filtered by category."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, description, category, tags,
                   views, likes, comments, created_at
            FROM videos
            WHERE category = ?
            ORDER BY views DESC
            LIMIT ?
        """, (category, limit))
        
        return [
            {
                'video_id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'category': row['category'],
                'tags': row['tags'].split(',') if row['tags'] else [],
                'views': row['views'],
                'likes': row['likes'],
                'comments': row['comments']
            }
            for row in cursor.fetchall()
        ]
    
    # ==================== Tag System ====================
    
    def get_all_tags(self) -> List[Dict]:
        """Get all tags with usage counts."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT tags FROM videos WHERE tags IS NOT NULL
        """)
        
        tag_counts: Dict[str, int] = {}
        for row in cursor.fetchall():
            if row['tags']:
                for tag in row['tags'].split(','):
                    tag = tag.strip().lower()
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Sort by count and return top tags
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'name': tag, 'count': count} for tag, count in sorted_tags[:100]]
    
    def filter_by_tag(self, tag: str, limit: int = 20) -> List[Dict]:
        """Get videos filtered by tag."""
        cursor = self.conn.cursor()
        
        # Search for tag in tags field (comma-separated)
        cursor.execute("""
            SELECT id, title, description, category, tags,
                   views, likes, comments, created_at
            FROM videos
            WHERE tags LIKE ?
            ORDER BY views DESC
            LIMIT ?
        """, (f"%{tag}%", limit))
        
        return [
            {
                'video_id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'category': row['category'],
                'tags': row['tags'].split(',') if row['tags'] else [],
                'views': row['views'],
                'likes': row['likes'],
                'comments': row['comments']
            }
            for row in cursor.fetchall()
        ]
    
    # ==================== Trending System ====================
    
    def get_trending_videos(self, timeframe: str = '24h', limit: int = 20) -> List[Dict]:
        """
        Get trending videos based on recent views and engagement.
        
        Args:
            timeframe: Time window ('1h', '24h', '7d', '30d')
            limit: Maximum number of results
        """
        cursor = self.conn.cursor()
        
        # Calculate time threshold
        now = datetime.now()
        if timeframe == '1h':
            threshold = now - timedelta(hours=1)
        elif timeframe == '24h':
            threshold = now - timedelta(days=1)
        elif timeframe == '7d':
            threshold = now - timedelta(days=7)
        elif timeframe == '30d':
            threshold = now - timedelta(days=30)
        else:
            threshold = now - timedelta(days=1)
        
        threshold_str = threshold.isoformat()
        
        # Get videos with recent view activity
        cursor.execute("""
            SELECT v.id, v.title, v.description, v.category, v.tags,
                   v.views, v.likes, v.comments, v.created_at,
                   COUNT(ve.id) as recent_views,
                   (v.likes + v.comments * 2) * 1.0 / MAX(v.views, 1) as engagement_rate
            FROM videos v
            LEFT JOIN view_events ve ON v.id = ve.video_id AND ve.viewed_at > ?
            GROUP BY v.id
            HAVING recent_views > 0
            ORDER BY (recent_views * 0.4 + engagement_rate * 0.4 + v.views * 0.2) DESC
            LIMIT ?
        """, (threshold_str, limit))
        
        return [
            {
                'video_id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'category': row['category'],
                'tags': row['tags'].split(',') if row['tags'] else [],
                'views': row['views'],
                'likes': row['likes'],
                'comments': row['comments'],
                'recent_views': row['recent_views'],
                'engagement_rate': row['engagement_rate'],
                'trending_score': row['recent_views'] * 0.4 + row['engagement_rate'] * 0.4 + row['views'] * 0.2
            }
            for row in cursor.fetchall()
        ]
    
    # ==================== "For You" Feed ====================
    
    def get_for_you_feed(self, user_id: int, limit: int = 20) -> List[Dict]:
        """
        Get personalized "For You" feed based on user's watch history.
        
        Args:
            user_id: User ID
            limit: Maximum number of results
        """
        cursor = self.conn.cursor()
        
        # Get user's watched categories
        cursor.execute("""
            SELECT v.category, COUNT(*) as watch_count
            FROM watch_history wh
            JOIN videos v ON wh.video_id = v.id
            WHERE wh.user_id = ?
            GROUP BY v.category
            ORDER BY watch_count DESC
            LIMIT 3
        """, (user_id,))
        
        preferred_categories = [row['category'] for row in cursor.fetchall()]
        
        # Get user's watched tags
        cursor.execute("""
            SELECT v.tags
            FROM watch_history wh
            JOIN videos v ON wh.video_id = v.id
            WHERE wh.user_id = ? AND v.tags IS NOT NULL
        """, (user_id,))
        
        watched_tags: Set[str] = set()
        for row in cursor.fetchall():
            if row['tags']:
                for tag in row['tags'].split(','):
                    watched_tags.add(tag.strip().lower())
        
        # Get videos already watched
        cursor.execute("""
            SELECT video_id FROM watch_history WHERE user_id = ?
        """, (user_id,))
        watched_ids = {row['video_id'] for row in cursor.fetchall()}
        
        # Get recommendations
        if preferred_categories:
            # Get videos from preferred categories
            placeholders = ','.join('?' * len(preferred_categories))
            cursor.execute(f"""
                SELECT id, title, description, category, tags,
                       views, likes, comments, created_at,
                       CASE
                           WHEN category IN ({placeholders}) THEN 2
                           ELSE 1
                       END as priority
                FROM videos
                WHERE id NOT IN ({','.join('?' * len(watched_ids))})
                ORDER BY priority, views DESC
                LIMIT ?
            """, (*preferred_categories, *watched_ids, limit * 2))
        else:
            # New user - return popular videos
            cursor.execute("""
                SELECT id, title, description, category, tags,
                       views, likes, comments, created_at,
                       1 as priority
                FROM videos
                ORDER BY views DESC
                LIMIT ?
            """, (limit * 2,))
        
        results = []
        for row in cursor.fetchall():
            if row['id'] not in watched_ids:
                # Calculate tag match score
                video_tags = set(row['tags'].split(',')) if row['tags'] else set()
                tag_match = len(video_tags & watched_tags)
                
                results.append({
                    'video_id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'category': row['category'],
                    'tags': list(video_tags),
                    'views': row['views'],
                    'likes': row['likes'],
                    'comments': row['comments'],
                    'priority': row['priority'],
                    'tag_match_score': tag_match,
                    'reason': f"From your favorite category: {row['category']}" if row['priority'] == 2 else "Popular video"
                })
        
        # Sort by priority and tag match
        results.sort(key=lambda x: (x['priority'], x['tag_match_score']), reverse=True)
        return results[:limit]
    
    # ==================== Agent Directory ====================
    
    def get_agents(self, filter_by: Optional[str] = None, sort_by: str = 'subscribers', limit: int = 20) -> List[Dict]:
        """
        Get agent directory with filtering and sorting.
        
        Args:
            filter_by: Filter by capability
            sort_by: Sort field ('subscribers', 'videos', 'activity')
            limit: Maximum number of results
        """
        cursor = self.conn.cursor()
        
        # Get agents with stats
        if filter_by:
            cursor.execute("""
                SELECT a.id, a.name, a.description, a.capabilities,
                       a.subscriber_count, a.video_count, a.last_active,
                       a.created_at
                FROM agents a
                WHERE a.capabilities LIKE ?
                ORDER BY subscriber_count DESC
                LIMIT ?
            """, (f"%{filter_by}%", limit))
        else:
            if sort_by == 'subscribers':
                order = 'subscriber_count DESC'
            elif sort_by == 'videos':
                order = 'video_count DESC'
            elif sort_by == 'activity':
                order = 'last_active DESC'
            else:
                order = 'subscriber_count DESC'
            
            cursor.execute(f"""
                SELECT id, name, description, capabilities,
                       subscriber_count, video_count, last_active,
                       created_at
                FROM agents
                ORDER BY {order}
                LIMIT ?
            """, (limit,))
        
        return [
            {
                'agent_id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'capabilities': row['capabilities'].split(',') if row['capabilities'] else [],
                'subscribers': row['subscriber_count'],
                'videos': row['video_count'],
                'last_active': row['last_active']
            }
            for row in cursor.fetchall()
        ]
    
    # ==================== API Routes Helper ====================
    
    def create_flask_routes(self, app):
        """Create Flask API routes for discoverability."""
        from flask import jsonify, request
        
        @app.route('/api/search', methods=['GET'])
        def api_search():
            """Search videos."""
            query = request.args.get('q', '')
            limit = request.args.get('limit', 20, type=int)
            
            if not query:
                return jsonify({'error': 'Query parameter q is required'}), 400
            
            results = self.search_videos(query, limit)
            return jsonify({'status': 'success', 'count': len(results), 'results': results})
        
        @app.route('/api/categories', methods=['GET'])
        def api_categories():
            """Get all categories."""
            categories = self.get_categories()
            return jsonify({'status': 'success', 'categories': categories})
        
        @app.route('/api/categories/<category>', methods=['GET'])
        def api_category_videos(category):
            """Get videos by category."""
            limit = request.args.get('limit', 20, type=int)
            videos = self.filter_by_category(category, limit)
            return jsonify({'status': 'success', 'count': len(videos), 'videos': videos})
        
        @app.route('/api/tags', methods=['GET'])
        def api_tags():
            """Get all tags."""
            tags = self.get_all_tags()
            return jsonify({'status': 'success', 'count': len(tags), 'tags': tags})
        
        @app.route('/api/tags/<tag>', methods=['GET'])
        def api_tag_videos(tag):
            """Get videos by tag."""
            limit = request.args.get('limit', 20, type=int)
            videos = self.filter_by_tag(tag, limit)
            return jsonify({'status': 'success', 'count': len(videos), 'videos': videos})
        
        @app.route('/api/trending', methods=['GET'])
        def api_trending():
            """Get trending videos."""
            timeframe = request.args.get('timeframe', '24h')
            limit = request.args.get('limit', 20, type=int)
            videos = self.get_trending_videos(timeframe, limit)
            return jsonify({'status': 'success', 'count': len(videos), 'videos': videos})
        
        @app.route('/api/for-you', methods=['GET'])
        def api_for_you():
            """Get personalized feed."""
            user_id = request.args.get('user_id', type=int)
            limit = request.args.get('limit', 20, type=int)
            
            if not user_id:
                return jsonify({'error': 'user_id parameter is required'}), 400
            
            feed = self.get_for_you_feed(user_id, limit)
            return jsonify({'status': 'success', 'count': len(feed), 'feed': feed})
        
        @app.route('/api/agents', methods=['GET'])
        def api_agents():
            """Get agent directory."""
            filter_by = request.args.get('capability', None)
            sort_by = request.args.get('sort', 'subscribers')
            limit = request.args.get('limit', 20, type=int)
            
            agents = self.get_agents(filter_by, sort_by, limit)
            return jsonify({'status': 'success', 'count': len(agents), 'agents': agents})


if __name__ == "__main__":
    # Example usage
    engine = DiscoverabilityEngine("bottube.db")
    
    # Setup FTS
    engine.setup_fts()
    
    # Search
    results = engine.search_videos("python tutorial")
    print(f"Search results: {len(results)}")
    
    # Categories
    categories = engine.get_categories()
    print(f"Categories: {categories}")
    
    # Trending
    trending = engine.get_trending_videos('24h', limit=10)
    print(f"Trending: {len(trending)}")
    
    engine.close()
