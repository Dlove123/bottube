#!/usr/bin/env python3
"""
BoTTube Video Page Customization Features
Implements:
- Custom themes (dark, light, neon, minimal)
- Layout options (cinema, theater, default)
- Font size adjustments
- Color scheme preferences
- Auto-play settings
- Playback speed defaults
"""

import json
import time
from typing import Dict, List, Optional
from flask import jsonify, request, session

# ── Theme Definitions ──

THEMES = {
    "default": {
        "name": "Default",
        "bg_primary": "#0f0f0f",
        "bg_secondary": "#1f1f1f",
        "text_primary": "#ffffff",
        "text_secondary": "#aaaaaa",
        "accent": "#ff0000",
        "css_file": "theme-default.css"
    },
    "dark": {
        "name": "Dark Mode",
        "bg_primary": "#121212",
        "bg_secondary": "#1e1e1e",
        "text_primary": "#e0e0e0",
        "text_secondary": "#a0a0a0",
        "accent": "#bb86fc",
        "css_file": "theme-dark.css"
    },
    "light": {
        "name": "Light Mode",
        "bg_primary": "#ffffff",
        "bg_secondary": "#f5f5f5",
        "text_primary": "#121212",
        "text_secondary": "#666666",
        "accent": "#1a73e8",
        "css_file": "theme-light.css"
    },
    "neon": {
        "name": "Neon Cyberpunk",
        "bg_primary": "#0a0a0f",
        "bg_secondary": "#1a1a2e",
        "text_primary": "#00ffff",
        "text_secondary": "#ff00ff",
        "accent": "#ffff00",
        "css_file": "theme-neon.css"
    },
    "minimal": {
        "name": "Minimal",
        "bg_primary": "#fafafa",
        "bg_secondary": "#ffffff",
        "text_primary": "#333333",
        "text_secondary": "#888888",
        "accent": "#4a90d9",
        "css_file": "theme-minimal.css"
    },
    "ocean": {
        "name": "Ocean Blue",
        "bg_primary": "#0d1b2a",
        "bg_secondary": "#1b263b",
        "text_primary": "#e0e1dd",
        "text_secondary": "#778da9",
        "accent": "#00b4d8",
        "css_file": "theme-ocean.css"
    }
}

LAYOUT_OPTIONS = {
    "default": {"name": "Default", "video_width": "640px", "sidebar": True},
    "theater": {"name": "Theater", "video_width": "960px", "sidebar": True},
    "cinema": {"name": "Cinema", "video_width": "100%", "sidebar": False},
    "focus": {"name": "Focus Mode", "video_width": "80%", "sidebar": False, "hide_comments": False}
}

FONT_SIZES = {
    "small": {"name": "Small", "base_size": "12px"},
    "medium": {"name": "Medium", "base_size": "14px"},
    "large": {"name": "Large", "base_size": "16px"},
    "xl": {"name": "Extra Large", "base_size": "18px"}
}

# ── User Preferences Helpers ──

def get_user_preferences(db, agent_id: int) -> Dict:
    """Get user's video page customization preferences."""
    
    prefs = db.execute("""
        SELECT preferences FROM agent_preferences
        WHERE agent_id = ?
    """, (agent_id,)).fetchone()
    
    if prefs and prefs["preferences"]:
        return json.loads(prefs["preferences"])
    
    # Default preferences
    return {
        "theme": "default",
        "layout": "default",
        "font_size": "medium",
        "auto_play": False,
        "playback_speed": 1.0,
        "show_captions": False,
        "hide_annotations": False
    }


def save_user_preferences(db, agent_id: int, preferences: Dict) -> bool:
    """Save user's video page customization preferences."""
    
    try:
        existing = db.execute("""
            SELECT id FROM agent_preferences WHERE agent_id = ?
        """, (agent_id,)).fetchone()
        
        if existing:
            db.execute("""
                UPDATE agent_preferences
                SET preferences = ?, updated_at = ?
                WHERE agent_id = ?
            """, (json.dumps(preferences), time.time(), agent_id))
        else:
            db.execute("""
                INSERT INTO agent_preferences (agent_id, preferences, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (agent_id, json.dumps(preferences), time.time(), time.time()))
        
        db.commit()
        return True
    except Exception as e:
        return False


def get_theme_css(theme_id: str) -> str:
    """Generate CSS for a theme."""
    
    theme = THEMES.get(theme_id, THEMES["default"])
    
    return f"""
:root {{
    --bg-primary: {theme['bg_primary']};
    --bg-secondary: {theme['bg_secondary']};
    --text-primary: {theme['text_primary']};
    --text-secondary: {theme['text_secondary']};
    --accent: {theme['accent']};
}}

body {{
    background-color: var(--bg-primary);
    color: var(--text-primary);
}}

.video-container {{
    background-color: var(--bg-secondary);
}}

.video-title {{
    color: var(--text-primary);
}}

.video-description {{
    color: var(--text-secondary);
}}

.btn-primary {{
    background-color: var(--accent);
    color: var(--bg-primary);
}}

.sidebar {{
    background-color: var(--bg-secondary);
}}

.comment {{
    border-bottom: 1px solid var(--bg-secondary);
}}
"""


def get_layout_css(layout_id: str) -> str:
    """Generate CSS for a layout."""
    
    layout = LAYOUT_OPTIONS.get(layout_id, LAYOUT_OPTIONS["default"])
    
    css = f"""
.video-wrapper {{
    max-width: {layout['video_width']};
    margin: 0 auto;
}}
"""
    
    if not layout.get("sidebar", True):
        css += """
.related-videos {{
    display: none;
}}

.video-wrapper {{
    max-width: 100%;
}}
"""
    
    if layout.get("hide_comments", False):
        css += """
.comments-section {{
    display: none;
}}
"""
    
    return css


def get_font_size_css(size_id: str) -> str:
    """Generate CSS for font size."""
    
    size = FONT_SIZES.get(size_id, FONT_SIZES["medium"])
    
    return f"""
:root {{
    --font-base: {size['base_size']};
}}

body {{
    font-size: var(--font-base);
}}

.video-title {{
    font-size: calc(var(--font-base) * 1.5);
}}

.video-description {{
    font-size: calc(var(--font-base) * 1.0);
}}

.comment-text {{
    font-size: calc(var(--font-base) * 0.9);
}}
"""


# ── API Route Registration ──

def register_customization_routes(app):
    """Register video customization routes with the Flask app."""
    
    @app.route("/api/preferences")
    def get_preferences():
        """Get current user's preferences."""
        prefs = get_user_preferences(g.db, g.agent["id"])
        return jsonify({"ok": True, "preferences": prefs})
    
    @app.route("/api/preferences", methods=["POST"])
    def save_preferences():
        """Save user's preferences."""
        data = request.get_json()
        
        # Validate and merge with defaults
        defaults = {
            "theme": "default",
            "layout": "default",
            "font_size": "medium",
            "auto_play": False,
            "playback_speed": 1.0,
            "show_captions": False,
            "hide_annotations": False
        }
        
        prefs = {**defaults, **data}
        
        # Validate theme
        if prefs["theme"] not in THEMES:
            prefs["theme"] = "default"
        
        # Validate layout
        if prefs["layout"] not in LAYOUT_OPTIONS:
            prefs["layout"] = "default"
        
        # Validate font size
        if prefs["font_size"] not in FONT_SIZES:
            prefs["font_size"] = "medium"
        
        # Validate playback speed
        try:
            prefs["playback_speed"] = float(prefs["playback_speed"])
            prefs["playback_speed"] = max(0.25, min(2.0, prefs["playback_speed"]))
        except (ValueError, TypeError):
            prefs["playback_speed"] = 1.0
        
        success = save_user_preferences(g.db, g.agent["id"], prefs)
        
        if success:
            return jsonify({"ok": True, "preferences": prefs})
        else:
            return jsonify({"error": "Failed to save preferences"}), 500
    
    @app.route("/api/themes")
    def list_themes():
        """List available themes."""
        themes_list = [
            {"id": k, "name": v["name"], "accent": v["accent"]}
            for k, v in THEMES.items()
        ]
        return jsonify({"ok": True, "themes": themes_list})
    
    @app.route("/api/themes/<theme_id>/css")
    def get_theme_css_route(theme_id):
        """Get CSS for a specific theme."""
        if theme_id not in THEMES:
            return jsonify({"error": "Theme not found"}), 404
        
        css = get_theme_css(theme_id)
        return Response(css, mimetype="text/css")
    
    @app.route("/api/layouts")
    def list_layouts():
        """List available layouts."""
        layouts_list = [
            {"id": k, "name": v["name"], "video_width": v["video_width"]}
            for k, v in LAYOUT_OPTIONS.items()
        ]
        return jsonify({"ok": True, "layouts": layouts_list})
    
    @app.route("/api/font-sizes")
    def list_font_sizes():
        """List available font sizes."""
        sizes_list = [
            {"id": k, "name": v["name"], "base_size": v["base_size"]}
            for k, v in FONT_SIZES.items()
        ]
        return jsonify({"ok": True, "sizes": sizes_list})
    
    @app.route("/api/customization/export")
    def export_customization():
        """Export user's customization as JSON."""
        prefs = get_user_preferences(g.db, g.agent["id"])
        
        export_data = {
            "version": "1.0",
            "agent_id": g.agent["id"],
            "exported_at": time.time(),
            "preferences": prefs
        }
        
        return jsonify(export_data)
    
    @app.route("/api/customization/import", methods=["POST"])
    def import_customization():
        """Import customization from JSON."""
        data = request.get_json()
        
        if not data or "preferences" not in data:
            return jsonify({"error": "Invalid import data"}), 400
        
        prefs = data["preferences"]
        success = save_user_preferences(g.db, g.agent["id"], prefs)
        
        if success:
            return jsonify({"ok": True, "preferences": prefs})
        else:
            return jsonify({"error": "Failed to import preferences"}), 500


# ── Template Helpers ──

def register_customization_template_helpers(app):
    """Register template helper functions."""
    
    @app.template_filter("theme_name")
    def theme_name_filter(theme_id: str) -> str:
        """Get theme display name."""
        return THEMES.get(theme_id, {}).get("name", theme_id)
    
    @app.template_filter("layout_name")
    def layout_name_filter(layout_id: str) -> str:
        """Get layout display name."""
        return LAYOUT_OPTIONS.get(layout_id, {}).get("name", layout_id)


# ── Database Schema ──

CUSTOMIZATION_SCHEMA = """
-- Agent preferences table (create if not exists)
CREATE TABLE IF NOT EXISTS agent_preferences (
    id INTEGER PRIMARY KEY,
    agent_id INTEGER UNIQUE NOT NULL,
    preferences TEXT NOT NULL DEFAULT '{}',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agent_preferences_agent ON agent_preferences(agent_id);
"""

# ── Schema Info ──

CUSTOMIZATION_SCHEMA_INFO = """
Video Page Customization - Schema changes required.

New table:
- agent_preferences (agent_id, preferences JSON, timestamps)

New API Endpoints:
- GET /api/preferences - Get user preferences
- POST /api/preferences - Save user preferences
- GET /api/themes - List available themes
- GET /api/themes/<id>/css - Get theme CSS
- GET /api/layouts - List available layouts
- GET /api/font-sizes - List font sizes
- GET /api/customization/export - Export preferences
- POST /api/customization/import - Import preferences

Features:
- 6 themes (default, dark, light, neon, minimal, ocean)
- 4 layouts (default, theater, cinema, focus)
- 4 font sizes (small, medium, large, xl)
- Auto-play toggle
- Playback speed default
- Export/Import preferences
"""

