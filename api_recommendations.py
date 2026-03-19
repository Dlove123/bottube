"""
BoTTube Recommendation API Routes
Integrates recommendation engine with BoTTube Flask app.
"""

from flask import Blueprint, jsonify, request
from recommendation_engine import RecommendationEngine

# Create blueprint
recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/api')

# Initialize engine (singleton)
_engine = None

def get_engine():
    """Get or create recommendation engine singleton."""
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
    return _engine


@recommendations_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """
    Get personalized recommendations for a user.
    
    Query Parameters:
        user_id (int): User ID to get recommendations for
        limit (int): Maximum number of recommendations (default: 20)
    
    Returns:
        JSON array of video recommendations with relevance scores
    """
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', 20, type=int)
    
    if not user_id:
        return jsonify({
            'error': 'user_id parameter is required',
            'status': 400
        }), 400
    
    try:
        engine = get_engine()
        recommendations = engine.get_personalized_feed(user_id, limit)
        
        return jsonify({
            'status': 'success',
            'count': len(recommendations),
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 500
        }), 500


@recommendations_bp.route('/trending', methods=['GET'])
def get_trending():
    """
    Get trending videos.
    
    Query Parameters:
        limit (int): Maximum number of videos (default: 20)
        category (str): Filter by category (optional)
    
    Returns:
        JSON array of trending videos with scores
    """
    limit = request.args.get('limit', 20, type=int)
    category = request.args.get('category', None)
    
    try:
        engine = get_engine()
        trending = engine.get_trending_videos(limit, category)
        
        return jsonify({
            'status': 'success',
            'count': len(trending),
            'trending': trending
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 500
        }), 500


@recommendations_bp.route('/similar', methods=['GET'])
def get_similar():
    """
    Get videos similar to a given video.
    
    Query Parameters:
        video_id (int): Video ID to find similar videos for
        limit (int): Maximum number of results (default: 10)
    
    Returns:
        JSON array of similar videos with similarity scores
    """
    video_id = request.args.get('video_id', type=int)
    limit = request.args.get('limit', 10, type=int)
    
    if not video_id:
        return jsonify({
            'error': 'video_id parameter is required',
            'status': 400
        }), 400
    
    try:
        engine = get_engine()
        similar = engine.get_similar_videos(video_id, limit)
        
        return jsonify({
            'status': 'success',
            'count': len(similar),
            'similar': similar
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 500
        }), 500


@recommendations_bp.route('/content-based', methods=['GET'])
def get_content_based():
    """
    Get content-based recommendations for a video.
    
    Query Parameters:
        video_id (int): Video ID to get recommendations for
        limit (int): Maximum number of results (default: 10)
    
    Returns:
        JSON array of videos with content similarity scores
    """
    video_id = request.args.get('video_id', type=int)
    limit = request.args.get('limit', 10, type=int)
    
    if not video_id:
        return jsonify({
            'error': 'video_id parameter is required',
            'status': 400
        }), 400
    
    try:
        engine = get_engine()
        recommendations = engine.get_content_based_recommendations(video_id, limit)
        
        return jsonify({
            'status': 'success',
            'count': len(recommendations),
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 500
        }), 500


@recommendations_bp.route('/collaborative', methods=['GET'])
def get_collaborative():
    """
    Get collaborative filtering recommendations for a user.
    
    Query Parameters:
        user_id (int): User ID to get recommendations for
        limit (int): Maximum number of results (default: 10)
    
    Returns:
        JSON array of videos with collaborative scores
    """
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', 10, type=int)
    
    if not user_id:
        return jsonify({
            'error': 'user_id parameter is required',
            'status': 400
        }), 400
    
    try:
        engine = get_engine()
        recommendations = engine.get_collaborative_recommendations(user_id, limit)
        
        return jsonify({
            'status': 'success',
            'count': len(recommendations),
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 500
        }), 500


def init_app(app):
    """Initialize the recommendations blueprint with the Flask app."""
    app.register_blueprint(recommendations_bp)
