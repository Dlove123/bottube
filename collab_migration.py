#!/usr/bin/env python3
"""
Migration script for BoTTube Creator Collaboration Features
Adds support for:
- Co-uploads with collaborator_ids
- Video responses/duets
- Shared/collaborative playlists
- Split tips for collaborators
"""

import sqlite3
import json
from pathlib import Path

def run_migration(db_path):
    """Run the collaboration features migration."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("Starting collaboration features migration...")
    
    # 1. Add collaborator_ids to videos table
    print("  [1/5] Adding collaborator_ids to videos table...")
    c.execute("""
        ALTER TABLE videos ADD COLUMN collaborator_ids TEXT DEFAULT '[]'
    """)
    print("    ✓ Added collaborator_ids column (JSON array of agent_ids)")
    
    # 2. Add response_to_video_id for duets/responses
    print("  [2/5] Adding response_to_video_id for video responses...")
    c.execute("""
        ALTER TABLE videos ADD COLUMN response_to_video_id TEXT DEFAULT NULL
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_videos_response ON videos(response_to_video_id)
    """)
    print("    ✓ Added response_to_video_id column (links to parent video)")
    
    # 3. Add collaborative flag to playlists
    print("  [3/5] Adding collaborative support to playlists...")
    c.execute("""
        ALTER TABLE playlists ADD COLUMN is_collaborative INTEGER DEFAULT 0
    """)
    print("    ✓ Added is_collaborative flag to playlists")
    
    # 4. Create playlist_members table for shared playlists
    print("  [4/5] Creating playlist_members table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS playlist_members (
            id INTEGER PRIMARY KEY,
            playlist_id INTEGER NOT NULL,
            agent_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member',  -- owner | member | editor
            added_at REAL NOT NULL,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_playlist_members_pl ON playlist_members(playlist_id)
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_playlist_members_agent ON playlist_members(agent_id)
    """)
    c.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_playlist_members_uniq ON playlist_members(playlist_id, agent_id)
    """)
    print("    ✓ Created playlist_members table (many-to-many for shared playlists)")
    
    # 5. Add split support to tips table
    print("  [5/5] Adding split tip support...")
    c.execute("""
        ALTER TABLE tips ADD COLUMN split_amount REAL DEFAULT NULL
    """)
    c.execute("""
        ALTER TABLE tips ADD COLUMN original_tip_id INTEGER DEFAULT NULL
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_tips_split ON tips(original_tip_id) WHERE original_tip_id IS NOT NULL
    """)
    print("    ✓ Added split_amount and original_tip_id for tip splitting")
    
    conn.commit()
    print("\n✅ Migration completed successfully!")
    print("\nNew features enabled:")
    print("  - Co-uploads: Multiple creators credited on one video")
    print("  - Video responses: Duets and response videos")
    print("  - Shared playlists: Multiple curators per playlist")
    print("  - Split tips: Automatic tip distribution to collaborators")
    
    conn.close()

if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "bottube.db"
    run_migration(db_path)
