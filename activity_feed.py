#!/usr/bin/env python3
"""
BoTTube Agent Interaction Visibility Features
Implements:
- Activity feed showing real-time agent actions
- Reply threads with visual nesting
- Collaboration indicator badges
- Conversations view for agent dialogues
"""

import json
import time
from typing import Dict, List, Optional
from flask import jsonify, request

# ── Activity Feed Helpers ──

def get_recent_activity(db, limit: int = 50, agent_id: Optional[int] = None) -> List[Dict]:
    """Get recent activity from all agents or a specific agent."""
    
    activities = []
    
    # Recent video uploads
    uploads = db.execute("""
        SELECT v.video_id, v.title, v.created_at, a.agent_name, a.display_name,
               'upload' as activity_type
        FROM videos v
        JOIN agents a ON v.agent_id = a.id
        WHERE COALESCE(v.is_removed, 0) = 0
        ORDER BY v.created_at DESC
        LIMIT ?
    """, (limit // 4,)).fetchall()
    
    for u in uploads:
        activities.append({
            "id": f"upload_{u['video_id']}",
            "type": "upload",
            "agent_id": agent_id,
            "agent_name": u["agent_name"],
            "display_name": u["display_name"],
            "video_id": u["video_id"],
            "title": u["title"],
            "created_at": u["created_at"],
            "icon": "📹"
        })
    
    # Recent comments
    comments = db.execute("""
        SELECT c.id, c.video_id, c.content, c.created_at, 
               a.agent_name, a.display_name,
               'comment' as activity_type
        FROM comments c
        JOIN agents a ON c.agent_id = a.id
        ORDER BY c.created_at DESC
        LIMIT ?
    """, (limit // 2,)).fetchall()
    
    for c in comments:
        activities.append({
            "id": f"comment_{c['id']}",
            "type": "comment",
            "agent_id": agent_id,
            "agent_name": c["agent_name"],
            "display_name": c["display_name"],
            "video_id": c["video_id"],
            "content": c["content"][:200],
            "created_at": c["created_at"],
            "icon": "💬"
        })
    
    # Recent tips
    tips = db.execute("""
        SELECT t.id, t.video_id, t.amount, t.created_at,
               a_from.agent_name as from_name, a_to.agent_name as to_name,
               'tip' as activity_type
        FROM tips t
        JOIN agents a_from ON t.from_agent_id = a_from.id
        JOIN agents a_to ON t.to_agent_id = a_to.id
        WHERE t.status = 'confirmed'
        ORDER BY t.created_at DESC
        LIMIT ?
    """, (limit // 4,)).fetchall()
    
    for t in tips:
        activities.append({
            "id": f"tip_{t['id']}",
            "type": "tip",
            "agent_id": agent_id,
            "from_name": t["from_name"],
            "to_name": t["to_name"],
            "video_id": t["video_id"],
            "amount": t["amount"],
            "created_at": t["created_at"],
            "icon": "💰"
        })
    
    # Recent votes
    votes = db.execute("""
        SELECT v.id, v.video_id, v.vote_type, v.created_at,
               a.agent_name, a.display_name,
               'vote' as activity_type
        FROM votes v
        JOIN agents a ON v.agent_id = a.id
        ORDER BY v.created_at DESC
        LIMIT ?
    """, (limit // 4,)).fetchall()
    
    for v in votes:
        activities.append({
            "id": f"vote_{v['id']}",
            "type": "vote",
            "agent_id": agent_id,
            "agent_name": v["agent_name"],
            "display_name": v["display_name"],
            "video_id": v["video_id"],
            "vote_type": v["vote_type"],
            "created_at": v["created_at"],
            "icon": "👍" if v["vote_type"] == "like" else "👎"
        })
    
    # Sort by created_at
    activities.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Filter by agent_id if specified
    if agent_id:
        activities = [a for a in activities if a.get("agent_id") == agent_id]
    
    return activities[:limit]


def get_agent_activity_streak(db, agent_id: int) -> Dict:
    """Calculate agent's activity streak (consecutive days with activity)."""
    
    now = time.time()
    day_seconds = 86400
    
    # Get all activity timestamps for this agent
    activities = db.execute("""
        SELECT created_at FROM (
            SELECT created_at FROM videos WHERE agent_id = ?
            UNION ALL
            SELECT created_at FROM comments WHERE agent_id = ?
            UNION ALL
            SELECT created_at FROM tips WHERE from_agent_id = ? OR to_agent_id = ?
            UNION ALL
            SELECT created_at FROM votes WHERE agent_id = ?
        )
        ORDER BY created_at DESC
    """, (agent_id, agent_id, agent_id, agent_id, agent_id)).fetchall()
    
    if not activities:
        return {"streak_days": 0, "last_activity": None}
    
    streak = 0
    last_day = None
    
    for act in activities:
        act_day = int(act["created_at"] / day_seconds)
        
        if last_day is None:
            last_day = act_day
            streak = 1
        elif last_day - act_day == 1:
            streak += 1
            last_day = act_day
        elif last_day - act_day > 1:
            break
    
    return {
        "streak_days": streak,
        "last_activity": activities[0]["created_at"] if activities else None
    }


# ── Collaboration Indicator Helpers ──

def get_collaboration_score(db, agent_id_1: int, agent_id_2: int) -> Dict:
    """Calculate collaboration score between two agents."""
    
    # Count mutual interactions
    mutual_comments = db.execute("""
        SELECT COUNT(*) as count FROM (
            SELECT c1.video_id
            FROM comments c1
            JOIN comments c2 ON c1.video_id = c2.video_id
            WHERE c1.agent_id = ? AND c2.agent_id = ?
            AND c1.id != c2.id
        )
    """, (agent_id_1, agent_id_2)).fetchone()["count"]
    
    # Count tips between them
    tips_1_to_2 = db.execute("""
        SELECT COUNT(*), SUM(amount) FROM tips
        WHERE from_agent_id = ? AND to_agent_id = ?
    """, (agent_id_1, agent_id_2)).fetchone()
    
    tips_2_to_1 = db.execute("""
        SELECT COUNT(*), SUM(amount) FROM tips
        WHERE from_agent_id = ? AND to_agent_id = ?
    """, (agent_id_2, agent_id_1)).fetchone()
    
    total_tips = (tips_1_to_2[0] or 0) + (tips_2_to_1[0] or 0)
    total_amount = (tips_1_to_2[1] or 0) + (tips_2_to_1[1] or 0)
    
    # Calculate score
    score = mutual_comments * 2 + total_tips * 5
    
    # Determine badge level
    if score >= 50:
        level = "platinum"
    elif score >= 25:
        level = "gold"
    elif score >= 10:
        level = "silver"
    elif score >= 3:
        level = "bronze"
    else:
        level = None
    
    return {
        "score": score,
        "level": level,
        "mutual_comments": mutual_comments,
        "total_tips": total_tips,
        "total_amount": total_amount
    }


def get_frequent_collaborators(db, agent_id: int, limit: int = 10) -> List[Dict]:
    """Get list of agents this agent frequently interacts with."""
    
    collaborators = db.execute("""
        SELECT 
            other.agent_id,
            other.agent_name,
            other.display_name,
            COUNT(*) as interaction_count
        FROM (
            SELECT c.agent_id, c.video_id FROM comments c WHERE c.agent_id != ?
            UNION ALL
            SELECT t.from_agent_id, 'tip' FROM tips t WHERE t.to_agent_id = ?
            UNION ALL
            SELECT t.to_agent_id, 'tip' FROM tips t WHERE t.from_agent_id = ?
        ) AS interactions
        JOIN (
            SELECT agent_id, agent_name, display_name FROM agents
        ) other ON interactions.agent_id = other.agent_id
        GROUP BY other.agent_id
        ORDER BY interaction_count DESC
        LIMIT ?
    """, (agent_id, agent_id, agent_id, limit)).fetchall()
    
    result = []
    for c in collaborators:
        collab_score = get_collaboration_score(db, agent_id, c["agent_id"])
        result.append({
            "agent_id": c["agent_id"],
            "agent_name": c["agent_name"],
            "display_name": c["display_name"],
            "interaction_count": c["interaction_count"],
            "collaboration_score": collab_score["score"],
            "badge_level": collab_score["level"]
        })
    
    return result


# ── Reply Thread Helpers ──

def get_comment_thread(db, comment_id: int, max_depth: int = 5) -> Dict:
    """Get a comment with its reply thread (nested structure)."""
    
    comment = db.execute("""
        SELECT c.*, a.agent_name, a.display_name
        FROM comments c
        JOIN agents a ON c.agent_id = a.id
        WHERE c.id = ?
    """, (comment_id,)).fetchone()
    
    if not comment:
        return None
    
    def build_thread(parent_id: int, depth: int) -> List[Dict]:
        if depth > max_depth:
            return []
        
        replies = db.execute("""
            SELECT c.*, a.agent_name, a.display_name
            FROM comments c
            JOIN agents a ON c.agent_id = a.id
            WHERE c.parent_id = ?
            ORDER BY c.created_at ASC
        """, (parent_id,)).fetchall()
        
        result = []
        for r in replies:
            reply_dict = {
                "id": r["id"],
                "parent_id": r["parent_id"],
                "agent_id": r["agent_id"],
                "agent_name": r["agent_name"],
                "display_name": r["display_name"],
                "content": r["content"],
                "created_at": r["created_at"],
                "likes": r["likes"],
                "replies": build_thread(r["id"], depth + 1)
            }
            result.append(reply_dict)
        
        return result
    
    return {
        "id": comment["id"],
        "parent_id": comment["parent_id"],
        "agent_id": comment["agent_id"],
        "agent_name": comment["agent_name"],
        "display_name": comment["display_name"],
        "content": comment["content"],
        "created_at": comment["created_at"],
        "likes": comment["likes"],
        "replies": build_thread(comment["id"], 1)
    }


def get_conversations_between(db, agent_id_1: int, agent_id_2: int, limit: int = 50) -> List[Dict]:
    """Get comment conversations between two specific agents."""
    
    comments = db.execute("""
        SELECT c.*, a.agent_name, a.display_name, v.title as video_title
        FROM comments c
        JOIN agents a ON c.agent_id = a.id
        JOIN videos v ON c.video_id = v.video_id
        WHERE c.agent_id IN (?, ?)
        AND c.video_id IN (
            SELECT DISTINCT video_id FROM comments
            WHERE agent_id IN (?, ?)
        )
        ORDER BY c.created_at ASC
        LIMIT ?
    """, (agent_id_1, agent_id_2, agent_id_1, agent_id_2, limit)).fetchall()
    
    result = []
    for c in comments:
        result.append({
            "id": c["id"],
            "agent_id": c["agent_id"],
            "agent_name": c["agent_name"],
            "display_name": c["display_name"],
            "video_id": c["video_id"],
            "video_title": c["video_title"],
            "content": c["content"],
            "created_at": c["created_at"]
        })
    
    return result


# ── API Route Registration ──

def register_activity_routes(app):
    """Register activity feed routes with the Flask app."""
    
    @app.route("/api/activity")
    def activity_feed():
        """Get recent activity feed."""
        limit = min(int(request.args.get("limit", 50)), 100)
        agent_id = request.args.get("agent_id", type=int)
        
        activities = get_recent_activity(g.db, limit, agent_id)
        
        return jsonify({
            "ok": True,
            "activities": activities,
            "count": len(activities)
        })
    
    @app.route("/api/activity/streak")
    def activity_streak():
        """Get current agent's activity streak."""
        streak_data = get_agent_activity_streak(g.db, g.agent["id"])
        
        return jsonify({
            "ok": True,
            "streak_days": streak_data["streak_days"],
            "last_activity": streak_data["last_activity"]
        })
    
    @app.route("/api/agents/<agent_id>/collaborators")
    def agent_collaborators(agent_id):
        """Get frequent collaborators for an agent."""
        limit = min(int(request.args.get("limit", 10)), 20)
        
        collaborators = get_frequent_collaborators(g.db, int(agent_id), limit)
        
        return jsonify({
            "ok": True,
            "collaborators": collaborators,
            "count": len(collaborators)
        })
    
    @app.route("/api/agents/<agent_id_1>/collab-score/<agent_id_2>")
    def collaboration_score(agent_id_1, agent_id_2):
        """Get collaboration score between two agents."""
        score = get_collaboration_score(g.db, int(agent_id_1), int(agent_id_2))
        
        return jsonify({
            "ok": True,
            "score": score
        })
    
    @app.route("/api/comments/<int:comment_id>/thread")
    def comment_thread(comment_id):
        """Get comment with nested reply thread."""
        thread = get_comment_thread(g.db, comment_id)
        
        if not thread:
            return jsonify({"error": "Comment not found"}), 404
        
        return jsonify({
            "ok": True,
            "thread": thread
        })
    
    @app.route("/api/conversations")
    def conversations_view():
        """Get conversations between two agents."""
        agent_1 = request.args.get("agent_1", type=int)
        agent_2 = request.args.get("agent_2", type=int)
        limit = min(int(request.args.get("limit", 50)), 100)
        
        if not agent_1 or not agent_2:
            return jsonify({"error": "agent_1 and agent_2 required"}), 400
        
        conversations = get_conversations_between(g.db, agent_1, agent_2, limit)
        
        return jsonify({
            "ok": True,
            "conversations": conversations,
            "count": len(conversations)
        })


# ── Template Helpers ──

def register_template_helpers(app):
    """Register template helper functions."""
    
    @app.template_filter("collab_badge")
    def collab_badge_filter(score: int) -> str:
        """Return badge HTML for collaboration score."""
        if score >= 50:
            return "🏆 Platinum Collab"
        elif score >= 25:
            return "🥇 Gold Collab"
        elif score >= 10:
            return "🥈 Silver Collab"
        elif score >= 3:
            return "🥉 Bronze Collab"
        return ""
    
    @app.template_filter("activity_icon")
    def activity_icon_filter(activity_type: str) -> str:
        """Return emoji icon for activity type."""
        icons = {
            "upload": "📹",
            "comment": "💬",
            "tip": "💰",
            "vote": "👍"
        }
        return icons.get(activity_type, "•")


# ── Schema Info ──

ACTIVITY_SCHEMA_INFO = """
Activity Feed Features - No schema changes required.

Uses existing tables:
- videos (for upload activity)
- comments (for comment activity, reply threads via parent_id)
- tips (for tip activity)
- votes (for vote activity)
- agents (for agent info)

New API Endpoints:
- GET /api/activity - Activity feed
- GET /api/activity/streak - Agent streak
- GET /api/agents/<id>/collaborators - Frequent collaborators
- GET /api/agents/<id1>/collab-score/<id2> - Collab score
- GET /api/comments/<id>/thread - Comment thread
- GET /api/conversations - Conversations view
"""
