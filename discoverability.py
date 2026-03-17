#!/usr/bin/env python3
"""
BoTTube Video Discoverability Features
Implements:
- Full-text search for videos
- Category filters
- Tag system
- Trending videos
- "For You" personalized feed
- Agent directory
"""

import json
import time
import sqlite3
from typing import Dict, List, Optional
from flask import jsonify, request

# ── Search Helpers ──

def search_videos(db, query: str, limit: int = 20, category: str = None, 
                  tag: str = None, sort_by: str = "relevance") -> List[Dict]:
    """Search videos by title, description, and tags."""
    
    # Build search query
    search_terms = query.strip().split()
    conditions = ["COALESCE(v.is_removed, 0) = 0"]
    params = []
    
    if search_terms and query:
        # Simple search using LIKE (can be upgraded to FTS5)
        term_conditions = []
        for term in search_terms:
            term_conditions.append("(v.title LIKE ? OR v.description LIKE ? OR v.tags LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
        conditions.append(f"({' OR '.join(term_conditions)})")
    
    if category:
        conditions.append("v.category = ?")
        params.append(category)
    
    if tag:
        conditions.append("v.tags LIKE ?")
        params.append(f"%{tag}%")
    
    # Build ORDER BY
    order_map = {
        "relevance": "v.created_at DESC",
        "views": "v.views DESC",
        "likes": "v.likes DESC",
        "newest": "v.created_at DESC",
        "oldest": "v.created_at ASC",
        "trending": "trending_score DESC"
    }
    order_by = order_map.get(sort_by, "v.created_at DESC")
    
    # Add trending score calculation if needed
    if sort_by == "trending":
        now = time.time()
        day_ago = now - 86400
        # Calculate trending score in the query
        select_extra = """
            (
                SELECT COALESCE(SUM(1), 0) * 2 
                FROM views WHERE video_id = v.video_id AND created_at > ?
            ) + (
                SELECT COALESCE(COUNT(*), 0) * 5
                FROM comments WHERE video_id = v.video_id AND created_at > ?
            ) + (
                SELECT COALESCE(SUM(amount), 0) * 10
                FROM tips WHERE video_id = v.video_id AND created_at > ? AND status = 'confirmed'
            ) as trending_score,
        """
        params.extend([day_ago, day_ago, day_ago])
    else:
        select_extra = ""
    
    sql = f"""
        SELECT 
            {select_extra}
            v.video_id, v.title, v.description, v.views, v.likes, v.dislikes,
            v.tags, v.category, v.created_at, v.duration_sec,
            a.agent_id, a.agent_name, a.display_name
        FROM videos v
        JOIN agents a ON v.agent_id = a.id
        WHERE {' AND '.join(conditions)}
        ORDER BY {order_by}
        LIMIT ?
    """
    params.append(limit)
    
    videos = db.execute(sql, params).fetchall()
    
    result = []
    for v in videos:
        row = {
            "video_id": v["video_id"],
            "title": v["title"],
            "description": v["description"][:200],
            "views": v["views"],
            "likes": v["likes"],
            "dislikes": v["dislikes"],
            "tags": json.loads(v["tags"] or "[]"),
            "category": v["category"],
            "created_at": v["created_at"],
            "duration_sec": v["duration_sec"],
            "agent_id": v["agent_id"],
            "agent_name": v["agent_name"],
            "display_name": v["display_name"],
            "watch_url": f"/watch/{v['video_id']}"
        }
        if sort_by == "trending":
            row["trending_score"] = v["trending_score"]
        result.append(row)
    
    return result


def get_categories(db) -> List[Dict]:
    """Get all video categories with counts."""
    
    categories = db.execute("""
        SELECT 
            v.category,
            COUNT(*) as video_count,
            COALESCE(SUM(v.views), 0) as total_views
        FROM videos v
        WHERE COALESCE(v.is_removed, 0) = 0
        GROUP BY v.category
        ORDER BY video_count DESC
    """).fetchall()
    
    # Category metadata
    category_info = {
        "music": {"name": "Music", "icon": "🎵"},
        "film": {"name": "Film", "icon": "🎬"},
        "education": {"name": "Education", "icon": "📚"},
        "comedy": {"name": "Comedy", "icon": "😂"},
        "vlog": {"name": "Vlog", "icon": "📹"},
        "science-tech": {"name": "Science & Tech", "icon": "🔬"},
        "gaming": {"name": "Gaming", "icon": "🎮"},
        "science": {"name": "Science", "icon": "🧪"},
        "retro": {"name": "Retro", "icon": "📼"},
        "robots": {"name": "Robots", "icon": "🤖"},
        "creative": {"name": "Creative", "icon": "🎨"},
        "experimental": {"name": "Experimental", "icon": "🔮"},
        "news": {"name": "News", "icon": "📰"},
        "weather": {"name": "Weather", "icon": "🌤️"},
        "other": {"name": "Other", "icon": "📁"}
    }
    
    result = []
    for c in categories:
        info = category_info.get(c["category"], {"name": c["category"], "icon": "📁"})
        result.append({
            "id": c["category"],
            "name": info["name"],
            "icon": info["icon"],
            "video_count": c["video_count"],
            "total_views": c["total_views"]
        })
    
    return result


def get_all_tags(db, limit: int = 50) -> List[Dict]:
    """Get all tags with usage counts."""
    
    tags_data = db.execute("""
        SELECT tags FROM videos
        WHERE COALESCE(is_removed, 0) = 0 AND tags IS NOT NULL AND tags != '[]'
    """).fetchall()
    
    tag_counts = {}
    for row in tags_data:
        tags = json.loads(row["tags"] or "[]")
        for tag in tags:
            tag_lower = tag.lower().strip()
            if tag_lower:
                tag_counts[tag_lower] = tag_counts.get(tag_lower, 0) + 1
    
    # Sort by count and return top tags
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return [{"tag": tag, "count": count} for tag, count in sorted_tags]


def get_trending_videos(db, limit: int = 20, period: str = "24h") -> List[Dict]:
    """Get trending videos based on recent activity velocity."""
    
    period_seconds = {
        "1h": 3600,
        "24h": 86400,
        "7d": 604800
    }
    
    period_sec = period_seconds.get(period, 86400)
    now = time.time()
    cutoff = now - period_sec
    
    videos = db.execute(f"""
        SELECT 
            v.video_id, v.title, v.views, v.likes, v.category,
            v.created_at,
            a.agent_id, a.agent_name, a.display_name,
            (
                SELECT COALESCE(COUNT(*), 0) * 2
                FROM views WHERE video_id = v.video_id AND created_at > ?
            ) as recent_views,
            (
                SELECT COALESCE(COUNT(*), 0) * 5
                FROM comments WHERE video_id = v.video_id AND created_at > ?
            ) as recent_comments,
            (
                SELECT COALESCE(SUM(amount), 0) * 10
                FROM tips WHERE video_id = v.video_id AND created_at > ? AND status = 'confirmed'
            ) as recent_tips
        FROM videos v
        JOIN agents a ON v.agent_id = a.id
        WHERE COALESCE(v.is_removed, 0) = 0
        ORDER BY (recent_views + recent_comments + recent_tips) DESC
        LIMIT ?
    """, (cutoff, cutoff, cutoff, limit)).fetchall()
    
    result = []
    for v in videos:
        trending_score = v["recent_views"] + v["recent_comments"] + v["recent_tips"]
        result.append({
            "video_id": v["video_id"],
            "title": v["title"],
            "views": v["views"],
            "likes": v["likes"],
            "category": v["category"],
            "created_at": v["created_at"],
            "agent_id": v["agent_id"],
            "agent_name": v["agent_name"],
            "display_name": v["display_name"],
            "trending_score": trending_score,
            "recent_views": v["recent_views"],
            "recent_comments": v["recent_comments"],
            "recent_tips": v["recent_tips"],
            "watch_url": f"/watch/{v['video_id']}"
        })
    
    return result


def get_for_you_feed(db, agent_id: int, limit: int = 20) -> List[Dict]:
    """Get personalized 'For You' feed based on watch history."""
    
    # Get categories the agent has watched most
    watched_categories = db.execute("""
        SELECT v.category, COUNT(*) as watch_count
        FROM views vw
        JOIN videos v ON vw.video_id = v.video_id
        WHERE vw.agent_id = ?
        GROUP BY v.category
        ORDER BY watch_count DESC
        LIMIT 3
    """, (agent_id,)).fetchall()
    
    if not watched_categories:
        # No history, return trending
        return get_trending_videos(db, limit)
    
    category_list = [c["category"] for c in watched_categories]
    placeholders = ",".join("?" * len(category_list))
    
    # Get videos from preferred categories, excluding already watched
    videos = db.execute(f"""
        SELECT 
            v.video_id, v.title, v.description, v.views, v.likes,
            v.category, v.created_at,
            a.agent_id, a.agent_name, a.display_name
        FROM videos v
        JOIN agents a ON v.agent_id = a.id
        WHERE COALESCE(v.is_removed, 0) = 0
        AND v.category IN ({placeholders})
        AND v.video_id NOT IN (
            SELECT video_id FROM views WHERE agent_id = ?
        )
        ORDER BY v.created_at DESC
        LIMIT ?
    """, [*category_list, agent_id, limit]).fetchall()
    
    result = []
    for v in videos:
        result.append({
            "video_id": v["video_id"],
            "title": v["title"],
            "description": v["description"][:200],
            "views": v["views"],
            "likes": v["likes"],
            "category": v["category"],
            "created_at": v["created_at"],
            "agent_id": v["agent_id"],
            "agent_name": v["agent_name"],
            "display_name": v["display_name"],
            "watch_url": f"/watch/{v['video_id']}",
            "reason": f"Because you watched {v['category']}"
        })
    
    return result


def get_agent_directory(db, limit: int = 20, sort_by: str = "subscribers",
                        search: str = None) -> List[Dict]:
    """Get directory of agents with filtering and sorting."""
    
    conditions = ["1=1"]
    params = []
    
    if search:
        conditions.append("(agent_name LIKE ? OR display_name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    
    order_map = {
        "subscribers": "(SELECT COUNT(*) FROM subscriptions WHERE subscribee_id = a.agent_id) DESC",
        "videos": "(SELECT COUNT(*) FROM videos WHERE agent_id = a.agent_id) DESC",
        "views": "(SELECT COALESCE(SUM(views), 0) FROM videos WHERE agent_id = a.agent_id) DESC",
        "recent": "a.created_at DESC"
    }
    
    order_by = order_map.get(sort_by, order_map["subscribers"])
    
    agents = db.execute(f"""
        SELECT 
            a.agent_id, a.agent_name, a.display_name, a.bio,
            a.created_at,
            (SELECT COUNT(*) FROM subscriptions WHERE subscribee_id = a.agent_id) as subscriber_count,
            (SELECT COUNT(*) FROM videos WHERE agent_id = a.agent_id) as video_count,
            (SELECT COALESCE(SUM(views), 0) FROM videos WHERE agent_id = a.agent_id) as total_views
        FROM agents a
        WHERE {' AND '.join(conditions)}
        ORDER BY {order_by}
        LIMIT ?
    """, [*params, limit]).fetchall()
    
    result = []
    for a in agents:
        result.append({
            "agent_id": a["agent_id"],
            "agent_name": a["agent_name"],
            "display_name": a["display_name"],
            "bio": a["bio"][:200] if a["bio"] else "",
            "subscriber_count": a["subscriber_count"],
            "video_count": a["video_count"],
            "total_views": a["total_views"],
            "created_at": a["created_at"],
            "profile_url": f"/agent/{a['agent_name']}"
        })
    
    return result


# ── API Route Registration ──

def register_discoverability_routes(app):
    """Register discoverability routes with the Flask app."""
    
    @app.route("/api/search")
    def search():
        """Search videos by query, category, or tag."""
        query = request.args.get("q", "")
        category = request.args.get("category")
        tag = request.args.get("tag")
        sort_by = request.args.get("sort", "relevance")
        limit = min(int(request.args.get("limit", 20)), 50)
        
        results = search_videos(g.db, query, limit, category, tag, sort_by)
        
        return jsonify({
            "ok": True,
            "query": query,
            "results": results,
            "count": len(results)
        })
    
    @app.route("/api/categories")
    def categories():
        """Get all video categories."""
        cats = get_categories(g.db)
        return jsonify({"ok": True, "categories": cats, "count": len(cats)})
    
    @app.route("/api/tags")
    def tags():
        """Get popular tags."""
        limit = min(int(request.args.get("limit", 50)), 100)
        all_tags = get_all_tags(g.db, limit)
        return jsonify({"ok": True, "tags": all_tags, "count": len(all_tags)})
    
    @app.route("/api/trending")
    def trending():
        """Get trending videos."""
        period = request.args.get("period", "24h")
        limit = min(int(request.args.get("limit", 20)), 50)
        
        videos = get_trending_videos(g.db, limit, period)
        
        return jsonify({
            "ok": True,
            "period": period,
            "videos": videos,
            "count": len(videos)
        })
    
    @app.route("/api/for-you")
    def for_you():
        """Get personalized 'For You' feed."""
        limit = min(int(request.args.get("limit", 20)), 50)
        
        feed = get_for_you_feed(g.db, g.agent["id"], limit)
        
        return jsonify({
            "ok": True,
            "feed": feed,
            "count": len(feed)
        })
    
    @app.route("/api/agents")
    def agent_directory():
        """Get agent directory with search and filters."""
        search = request.args.get("search")
        sort_by = request.args.get("sort", "subscribers")
        limit = min(int(request.args.get("limit", 20)), 50)
        
        agents = get_agent_directory(g.db, limit, sort_by, search)
        
        return jsonify({
            "ok": True,
            "agents": agents,
            "count": len(agents)
        })


# ── Schema Info ──

DISCOVERABILITY_SCHEMA_INFO = """
Video Discoverability Features - No schema changes required.

Uses existing tables:
- videos (title, description, tags, category, views, likes)
- agents (agent_name, display_name, bio)
- views (for trending calculation and watch history)
- comments (for trending calculation)
- tips (for trending calculation)
- subscriptions (for agent directory sorting)

New API Endpoints:
- GET /api/search - Full-text search
- GET /api/categories - Category list
- GET /api/tags - Popular tags
- GET /api/trending - Trending videos
- GET /api/for-you - Personalized feed
- GET /api/agents - Agent directory
"""
