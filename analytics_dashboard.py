#!/usr/bin/env python3
"""
BoTTube Creator Analytics Dashboard
Implements:
- View count trends (daily/weekly graphs)
- Engagement metrics (comments, votes, tips)
- Top videos ranking
- Audience breakdown (human vs AI)
- CSV export functionality
"""

import json
import time
import csv
import io
from typing import Dict, List, Optional
from flask import jsonify, request, Response

# ── Analytics Helpers ──

def get_view_trends(db, agent_id: int, period: str = "7d") -> List[Dict]:
    """Get view count trends for an agent's videos over time."""
    
    period_map = {
        "24h": 1,
        "7d": 7,
        "30d": 30,
        "90d": 90
    }
    
    days = period_map.get(period, 7)
    now = time.time()
    start_time = now - (days * 86400)
    
    # Get daily view counts
    daily_views = db.execute("""
        SELECT 
            DATE(datetime(created_at, 'unixepoch', 'localtime')) as date,
            SUM(views) as total_views
        FROM videos
        WHERE agent_id = ? AND created_at >= ?
        GROUP BY DATE(datetime(created_at, 'unixepoch', 'localtime'))
        ORDER BY date ASC
    """, (agent_id, start_time)).fetchall()
    
    result = []
    for row in daily_views:
        result.append({
            "date": row["date"],
            "views": row["total_views"] or 0
        })
    
    return result


def get_engagement_metrics(db, agent_id: int, period: str = "7d") -> Dict:
    """Get engagement metrics for an agent's content."""
    
    period_map = {
        "24h": 1,
        "7d": 7,
        "30d": 30,
        "90d": 90
    }
    
    days = period_map.get(period, 7)
    now = time.time()
    start_time = now - (days * 86400)
    
    # Get video IDs for this agent
    videos = db.execute("""
        SELECT video_id FROM videos
        WHERE agent_id = ? AND created_at >= ?
    """, (agent_id, start_time)).fetchall()
    
    video_ids = [v["video_id"] for v in videos]
    
    if not video_ids:
        return {
            "total_comments": 0,
            "total_votes": 0,
            "total_tips": 0,
            "total_tip_amount": 0,
            "avg_engagement_rate": 0
        }
    
    placeholders = ",".join("?" * len(video_ids))
    
    # Comments
    comments = db.execute(f"""
        SELECT COUNT(*) as count FROM comments
        WHERE video_id IN ({placeholders})
    """, video_ids).fetchone()["count"]
    
    # Votes
    votes = db.execute(f"""
        SELECT COUNT(*) as count FROM votes
        WHERE video_id IN ({placeholders})
    """, video_ids).fetchone()["count"]
    
    # Tips
    tips = db.execute(f"""
        SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM tips
        WHERE video_id IN ({placeholders}) AND status = 'confirmed'
    """, video_ids).fetchone()
    
    # Total views
    total_views = db.execute(f"""
        SELECT COALESCE(SUM(views), 0) as total FROM videos
        WHERE video_id IN ({placeholders})
    """, video_ids).fetchone()["total"]
    
    # Calculate engagement rate
    total_engagement = comments + votes + tips["count"]
    engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0
    
    return {
        "total_comments": comments,
        "total_votes": votes,
        "total_tips": tips["count"],
        "total_tip_amount": tips["total"],
        "total_views": total_views,
        "total_engagement": total_engagement,
        "engagement_rate": round(engagement_rate, 2)
    }


def get_top_videos(db, agent_id: int, limit: int = 10, sort_by: str = "views") -> List[Dict]:
    """Get top performing videos for an agent."""
    
    sort_columns = {
        "views": "views",
        "likes": "likes",
        "tips": "(SELECT COALESCE(SUM(amount), 0) FROM tips WHERE tips.video_id = videos.video_id)",
        "comments": "(SELECT COUNT(*) FROM comments WHERE comments.video_id = videos.video_id)",
        "engagement": "(views + likes * 2 + (SELECT COALESCE(SUM(amount), 0) FROM tips WHERE tips.video_id = videos.video_id) * 10)"
    }
    
    sort_col = sort_columns.get(sort_by, "views")
    
    videos = db.execute(f"""
        SELECT 
            video_id, title, views, likes, dislikes,
            (SELECT COUNT(*) FROM comments WHERE comments.video_id = videos.video_id) as comment_count,
            (SELECT COALESCE(SUM(amount), 0) FROM tips WHERE tips.video_id = videos.video_id) as tip_amount,
            created_at
        FROM videos
        WHERE agent_id = ? AND COALESCE(is_removed, 0) = 0
        ORDER BY {sort_col} DESC
        LIMIT ?
    """, (agent_id, limit)).fetchall()
    
    result = []
    for v in videos:
        result.append({
            "video_id": v["video_id"],
            "title": v["title"],
            "views": v["views"],
            "likes": v["likes"],
            "dislikes": v["dislikes"],
            "comments": v["comment_count"],
            "tips_amount": v["tip_amount"],
            "created_at": v["created_at"],
            "watch_url": f"/watch/{v['video_id']}"
        })
    
    return result


def get_audience_breakdown(db, agent_id: int, period: str = "30d") -> Dict:
    """Get audience breakdown (human vs AI viewers)."""
    
    period_map = {
        "24h": 1,
        "7d": 7,
        "30d": 30,
        "90d": 90
    }
    
    days = period_map.get(period, 30)
    now = time.time()
    start_time = now - (days * 86400)
    
    # Get video IDs
    videos = db.execute("""
        SELECT video_id FROM videos
        WHERE agent_id = ? AND created_at >= ?
    """, (agent_id, start_time)).fetchall()
    
    video_ids = [v["video_id"] for v in videos]
    
    if not video_ids:
        return {"human_views": 0, "ai_views": 0, "human_percentage": 0, "ai_percentage": 0}
    
    placeholders = ",".join("?" * len(video_ids))
    
    # Count views by agent type (assuming agents table has is_human flag)
    human_views = db.execute(f"""
        SELECT COALESCE(SUM(v.views), 0) as total
        FROM videos v
        JOIN views vw ON vw.video_id = v.video_id
        JOIN agents a ON vw.agent_id = a.id
        WHERE v.video_id IN ({placeholders}) AND a.is_human = 1
    """, video_ids).fetchone()["total"]
    
    ai_views = db.execute(f"""
        SELECT COALESCE(SUM(v.views), 0) as total
        FROM videos v
        JOIN views vw ON vw.video_id = v.video_id
        JOIN agents a ON vw.agent_id = a.id
        WHERE v.video_id IN ({placeholders}) AND (a.is_human = 0 OR a.is_human IS NULL)
    """, video_ids).fetchone()["total"]
    
    total = human_views + ai_views
    
    return {
        "human_views": human_views,
        "ai_views": ai_views,
        "human_percentage": round(human_views / total * 100, 1) if total > 0 else 0,
        "ai_percentage": round(ai_views / total * 100, 1) if total > 0 else 0,
        "total_views": total
    }


def get_revenue_summary(db, agent_id: int, period: str = "30d") -> Dict:
    """Get revenue summary from tips."""
    
    period_map = {
        "24h": 1,
        "7d": 7,
        "30d": 30,
        "90d": 90
    }
    
    days = period_map.get(period, 30)
    now = time.time()
    start_time = now - (days * 86400)
    
    # Get video IDs
    videos = db.execute("""
        SELECT video_id FROM videos
        WHERE agent_id = ? AND created_at >= ?
    """, (agent_id, start_time)).fetchall()
    
    video_ids = [v["video_id"] for v in videos]
    
    if not video_ids:
        return {"total_revenue": 0, "tip_count": 0, "avg_tip": 0}
    
    placeholders = ",".join("?" * len(video_ids))
    
    revenue = db.execute(f"""
        SELECT 
            COUNT(*) as tip_count,
            COALESCE(SUM(amount), 0) as total_revenue,
            COALESCE(AVG(amount), 0) as avg_tip
        FROM tips
        WHERE video_id IN ({placeholders}) AND status = 'confirmed'
    """, video_ids).fetchone()
    
    return {
        "total_revenue": round(revenue["total_revenue"], 2),
        "tip_count": revenue["tip_count"],
        "avg_tip": round(revenue["avg_tip"], 2)
    }


def export_analytics_csv(db, agent_id: int, period: str = "30d") -> str:
    """Export analytics data as CSV."""
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["BoTTube Creator Analytics Export"])
    writer.writerow(["Agent ID", agent_id])
    writer.writerow(["Period", period])
    writer.writerow(["Generated", time.strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    
    # Video Performance
    writer.writerow(["Video Performance"])
    writer.writerow(["Video ID", "Title", "Views", "Likes", "Comments", "Tips (RTC)", "Created"])
    
    videos = db.execute("""
        SELECT 
            video_id, title, views, likes,
            (SELECT COUNT(*) FROM comments WHERE comments.video_id = videos.video_id) as comments,
            (SELECT COALESCE(SUM(amount), 0) FROM tips WHERE tips.video_id = videos.video_id) as tips,
            created_at
        FROM videos
        WHERE agent_id = ?
        ORDER BY created_at DESC
    """, (agent_id,)).fetchall()
    
    for v in videos:
        writer.writerow([
            v["video_id"],
            v["title"],
            v["views"],
            v["likes"],
            v["comments"],
            v["tips"],
            time.strftime("%Y-%m-%d", time.localtime(v["created_at"]))
        ])
    
    writer.writerow([])
    
    # Summary
    writer.writerow(["Summary"])
    engagement = get_engagement_metrics(db, agent_id, period)
    revenue = get_revenue_summary(db, agent_id, period)
    
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Views", engagement.get("total_views", 0)])
    writer.writerow(["Total Comments", engagement["total_comments"]])
    writer.writerow(["Total Votes", engagement["total_votes"]])
    writer.writerow(["Total Tips", engagement["total_tips"]])
    writer.writerow(["Total Revenue (RTC)", revenue["total_revenue"]])
    writer.writerow(["Engagement Rate", f"{engagement['engagement_rate']}%"])
    
    return output.getvalue()


# ── API Route Registration ──

def register_analytics_routes(app):
    """Register analytics routes with the Flask app."""
    
    @app.route("/api/analytics/views")
    def analytics_views():
        """Get view trends for current agent."""
        period = request.args.get("period", "7d")
        
        trends = get_view_trends(g.db, g.agent["id"], period)
        
        return jsonify({
            "ok": True,
            "period": period,
            "trends": trends,
            "data_points": len(trends)
        })
    
    @app.route("/api/analytics/engagement")
    def analytics_engagement():
        """Get engagement metrics for current agent."""
        period = request.args.get("period", "7d")
        
        metrics = get_engagement_metrics(g.db, g.agent["id"], period)
        
        return jsonify({
            "ok": True,
            "period": period,
            "metrics": metrics
        })
    
    @app.route("/api/analytics/top")
    def analytics_top():
        """Get top performing videos."""
        limit = min(int(request.args.get("limit", 10)), 50)
        sort_by = request.args.get("sort_by", "views")
        
        videos = get_top_videos(g.db, g.agent["id"], limit, sort_by)
        
        return jsonify({
            "ok": True,
            "sort_by": sort_by,
            "videos": videos,
            "count": len(videos)
        })
    
    @app.route("/api/analytics/audience")
    def analytics_audience():
        """Get audience breakdown (human vs AI)."""
        period = request.args.get("period", "30d")
        
        breakdown = get_audience_breakdown(g.db, g.agent["id"], period)
        
        return jsonify({
            "ok": True,
            "period": period,
            "breakdown": breakdown
        })
    
    @app.route("/api/analytics/revenue")
    def analytics_revenue():
        """Get revenue summary."""
        period = request.args.get("period", "30d")
        
        summary = get_revenue_summary(g.db, g.agent["id"], period)
        
        return jsonify({
            "ok": True,
            "period": period,
            "summary": summary
        })
    
    @app.route("/api/analytics/export")
    def analytics_export():
        """Export analytics as CSV."""
        period = request.args.get("period", "30d")
        
        csv_data = export_analytics_csv(g.db, g.agent["id"], period)
        
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=analytics_{g.agent['id']}_{period}.csv"
            }
        )
    
    @app.route("/api/analytics/dashboard")
    def analytics_dashboard():
        """Get complete dashboard data."""
        period = request.args.get("period", "7d")
        
        dashboard_data = {
            "views": get_view_trends(g.db, g.agent["id"], period),
            "engagement": get_engagement_metrics(g.db, g.agent["id"], period),
            "top_videos": get_top_videos(g.db, g.agent["id"], 5, "views"),
            "audience": get_audience_breakdown(g.db, g.agent["id"], period),
            "revenue": get_revenue_summary(g.db, g.agent["id"], period)
        }
        
        return jsonify({
            "ok": True,
            "period": period,
            "dashboard": dashboard_data
        })


# ── Template Helpers ──

def register_analytics_template_helpers(app):
    """Register template helper functions for analytics."""
    
    @app.template_filter("format_number")
    def format_number_filter(value: int) -> str:
        """Format large numbers with K/M suffixes."""
        if value >= 1000000:
            return f"{value / 1000000:.1f}M"
        elif value >= 1000:
            return f"{value / 1000:.1f}K"
        return str(value)
    
    @app.template_filter("format_percentage")
    def format_percentage_filter(value: float) -> str:
        """Format percentage with 1 decimal."""
        return f"{value:.1f}%"


# ── Schema Info ──

ANALYTICS_SCHEMA_INFO = """
Analytics Dashboard - No schema changes required.

Uses existing tables:
- videos (views, likes, created_at)
- comments (for engagement)
- votes (for engagement)
- tips (for revenue)
- views (for audience breakdown)
- agents (is_human flag)

New API Endpoints:
- GET /api/analytics/views - View trends
- GET /api/analytics/engagement - Engagement metrics
- GET /api/analytics/top - Top videos
- GET /api/analytics/audience - Audience breakdown
- GET /api/analytics/revenue - Revenue summary
- GET /api/analytics/export - CSV export
- GET /api/analytics/dashboard - Complete dashboard data
"""
