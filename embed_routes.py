"""
BoTTube Embed Routes - Bounty #2281
Embeddable player widget for external sites
"""

from flask import Blueprint, render_template, jsonify, request, url_for
import sqlite3

embed_bp = Blueprint('embed', __name__)

DB_PATH = 'bottube.db'

def get_video(video_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''SELECT id, title, video_url, mime_type, uploader FROM videos WHERE id = ?''', (video_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

@embed_bp.route('/embed/<video_id>')
def embed_video(video_id):
    video = get_video(video_id)
    return render_template('embed.html', video=video) if video else ('Video not found', 404)

@embed_bp.route('/oembed')
def oembed():
    url = request.args.get('url', '')
    video_id = url.split('/watch/')[-1].split('?')[0] if '/watch/' in url else None
    if not video_id: return jsonify({'error': 'Invalid URL'}), 400
    video = get_video(video_id)
    if not video: return jsonify({'error': 'Video not found'}), 404
    return jsonify({'type': 'video', 'version': '1.0', 'title': video['title'], 'author_name': video.get('uploader', 'Unknown'), 'provider_name': 'BoTTube', 'provider_url': 'https://bottube.ai', 'html': f'<iframe width="560" height="315" src="https://bottube.ai/embed/{video_id}" frameborder="0" allowfullscreen></iframe>', 'width': 560, 'height': 315})

@embed_bp.route('/embed-code/<video_id>')
def embed_code(video_id):
    video = get_video(video_id)
    if not video: return jsonify({'error': 'Video not found'}), 404
    return jsonify({'video_id': video_id, 'sizes': [{'name': 'Small', 'width': 420, 'height': 236}, {'name': 'Medium', 'width': 560, 'height': 315}], 'iframe_template': '<iframe width="{width}" height="{height}" src="https://bottube.ai/embed/{video_id}" frameborder="0" allowfullscreen></iframe>''})
