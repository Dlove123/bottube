# BoTTube Recommendation Engine

AI-powered recommendation system with content-based filtering, collaborative filtering, and trending algorithms.

## Features

### 1. Content-Based Filtering
- Analyzes video titles, descriptions, and tags
- Extracts keywords using NLP techniques
- Calculates similarity based on keyword overlap and category match
- Returns videos with similar content

### 2. Collaborative Filtering
- "Users who watched X also watched Y"
- Finds users with similar watch history
- Recommends videos watched by similar users
- Improves with more user data

### 3. Trending Algorithm
- Time-weighted view count
- Engagement rate (likes + comments / views)
- Velocity (recent views vs historical average)
- Recency boost for new content

### 4. Personalized Feed
- Combines content-based (40%), collaborative (40%), and trending (20%)
- Generates "For You" feed for each user
- Updates in real-time based on watch history

## API Endpoints

### GET /api/recommendations
Get personalized recommendations for a user.

**Parameters:**
- `user_id` (required): User ID
- `limit` (optional): Max results (default: 20)

**Example:**
```bash
curl "http://localhost:5000/api/recommendations?user_id=1&limit=10"
```

**Response:**
```json
{
  "status": "success",
  "count": 10,
  "recommendations": [
    {
      "video_id": 42,
      "title": "Advanced Python Tips",
      "relevance_score": 0.85,
      "views": 500,
      "category": "Education"
    }
  ]
}
```

### GET /api/trending
Get trending videos.

**Parameters:**
- `limit` (optional): Max results (default: 20)
- `category` (optional): Filter by category

**Example:**
```bash
curl "http://localhost:5000/api/trending?limit=10&category=Education"
```

### GET /api/similar
Get videos similar to a given video.

**Parameters:**
- `video_id` (required): Video ID
- `limit` (optional): Max results (default: 10)

**Example:**
```bash
curl "http://localhost:5000/api/similar?video_id=42&limit=10"
```

### GET /api/content-based
Get content-based recommendations.

**Parameters:**
- `video_id` (required): Video ID
- `limit` (optional): Max results (default: 10)

### GET /api/collaborative
Get collaborative filtering recommendations.

**Parameters:**
- `user_id` (required): User ID
- `limit` (optional): Max results (default: 10)

## Usage

### Basic Usage
```python
from recommendation_engine import RecommendationEngine

# Initialize engine
engine = RecommendationEngine("bottube.db")

# Get personalized feed
feed = engine.get_personalized_feed(user_id=1, limit=20)

# Get trending videos
trending = engine.get_trending_videos(limit=10)

# Get similar videos
similar = engine.get_similar_videos(video_id=42, limit=10)

# Close connection
engine.close()
```

### Flask Integration
```python
from flask import Flask
from api_recommendations import init_app

app = Flask(__name__)
init_app(app)

if __name__ == "__main__":
    app.run(debug=True)
```

## Algorithm Details

### Content Similarity
Uses Jaccard similarity for keyword and tag overlap:
```
similarity = |A ∩ B| / |A ∪ B|
```

Weighted combination:
- 40% keyword similarity
- 40% tag similarity
- 20% category match

### Collaborative Filtering
1. Find users with similar watch history
2. Use Jaccard similarity for user matching
3. Aggregate videos watched by similar users
4. Score by similarity weight

### Trending Score
```
score = 0.3 * log(views) + 
        0.3 * engagement_rate * 100 + 
        0.2 * velocity * 10 + 
        0.2 * time_decay * 10
```

Where:
- `engagement_rate = (likes + comments * 2) / views`
- `velocity = recent_views / total_views`
- `time_decay = exp(-age_hours / 168)` (1 week half-life)

## Testing

Run tests:
```bash
python -m pytest tests/test_recommendation_engine.py -v
```

Or with unittest:
```bash
python tests/test_recommendation_engine.py
```

## Performance

- Content-based: O(n) where n = number of videos
- Collaborative: O(u * v) where u = users, v = avg videos per user
- Trending: O(n) with caching support
- Personalized: O(n) combining all three

### Optimization Tips
1. Cache trending scores (update every 5 minutes)
2. Pre-compute user similarities (update hourly)
3. Use database indexes on watch_history
4. Limit result sets early in queries

## Database Schema

Required tables:
```sql
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
);

CREATE TABLE watch_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    video_id INTEGER NOT NULL,
    watched_at TEXT
);

CREATE TABLE view_events (
    id INTEGER PRIMARY KEY,
    video_id INTEGER NOT NULL,
    viewed_at TEXT
);
```

## Future Improvements

1. **Machine Learning Integration**
   - Train neural collaborative filtering model
   - Use embeddings for content similarity
   - A/B testing framework

2. **Real-time Updates**
   - WebSocket for live recommendation updates
   - Stream processing for view events

3. **Advanced Features**
   - Diversity filtering (avoid echo chambers)
   - Cold start handling for new users/videos
   - Multi-armed bandit for exploration

## License

MIT License - Part of BoTTube Project
