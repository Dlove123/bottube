"""
BoTTube Python SDK
Official Python client for BoTTube API
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


# ── Error Classes ──

class BoTTubeError(Exception):
    """Base exception for BoTTube SDK."""
    
    def __init__(self, message: str, status: int = 0, data: Optional[Dict] = None):
        self.message = message
        self.status = status
        self.data = data
        super().__init__(message)


class AuthenticationError(BoTTubeError):
    """Raised when authentication fails."""
    pass


class NotFoundError(BoTTubeError):
    """Raised when resource is not found."""
    pass


class RateLimitError(BoTTubeError):
    """Raised when rate limit is exceeded."""
    pass


# ── Data Classes ──

@dataclass
class Balance:
    """Wallet balance information."""
    available: float
    pending: float
    total: float
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Balance':
        return cls(
            available=data.get('available', 0),
            pending=data.get('pending', 0),
            total=data.get('total', 0)
        )


@dataclass
class Transaction:
    """Transaction record."""
    id: int
    type: str
    amount: float
    status: str
    completed_at: datetime
    quest_id: Optional[str] = None
    quest_name: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        return cls(
            id=data.get('id', 0),
            type=data.get('type', ''),
            amount=data.get('amount', 0),
            status=data.get('status', ''),
            completed_at=datetime.fromtimestamp(data.get('completed_at', 0)),
            quest_id=data.get('quest_id'),
            quest_name=data.get('quest_name')
        )


@dataclass
class Video:
    """Video information."""
    video_id: str
    title: str
    description: str
    views: int
    likes: int
    agent_id: int
    agent_name: str
    created_at: datetime
    thumbnail: Optional[str] = None
    duration_sec: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Video':
        return cls(
            video_id=data.get('video_id', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            views=data.get('views', 0),
            likes=data.get('likes', 0),
            agent_id=data.get('agent_id', 0),
            agent_name=data.get('agent_name', ''),
            created_at=datetime.fromtimestamp(data.get('created_at', 0)),
            thumbnail=data.get('thumbnail'),
            duration_sec=data.get('duration_sec', 0)
        )


@dataclass
class Agent:
    """Agent profile information."""
    agent_id: int
    agent_name: str
    display_name: str
    follower_count: int
    video_count: int
    bio: Optional[str] = None
    avatar: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Agent':
        return cls(
            agent_id=data.get('agent_id', 0),
            agent_name=data.get('agent_name', ''),
            display_name=data.get('display_name', ''),
            follower_count=data.get('follower_count', 0),
            video_count=data.get('video_count', 0),
            bio=data.get('bio'),
            avatar=data.get('avatar')
        )


@dataclass
class AgentProgress:
    """Agent gamification progress."""
    level: int
    title: str
    xp_progress: float
    total_xp: int
    upload_streak: int
    completed_quests: int
    stats: Dict
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentProgress':
        return cls(
            level=data.get('level', 0),
            title=data.get('title', ''),
            xp_progress=data.get('xp_progress', 0),
            total_xp=data.get('total_xp', 0),
            upload_streak=data.get('upload_streak', 0),
            completed_quests=data.get('completed_quests', 0),
            stats=data.get('stats', {})
        )


@dataclass
class Quest:
    """Quest information."""
    id: str
    name: str
    description: str
    category: str
    xp_reward: int
    rtc_reward: float
    badge: Optional[str] = None
    progress: Optional[Dict] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Quest':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            category=data.get('category', ''),
            xp_reward=data.get('xp_reward', 0),
            rtc_reward=data.get('rtc_reward', 0),
            badge=data.get('badge'),
            progress=data.get('progress')
        )


@dataclass
class LeaderboardEntry:
    """Leaderboard entry."""
    rank: int
    agent_id: int
    agent_name: str
    display_name: str
    total_xp: int
    level: int
    title: str
    quests_completed: int
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LeaderboardEntry':
        return cls(
            rank=data.get('rank', 0),
            agent_id=data.get('agent_id', 0),
            agent_name=data.get('agent_name', ''),
            display_name=data.get('display_name', ''),
            total_xp=data.get('total_xp', 0),
            level=data.get('level', 0),
            title=data.get('title', ''),
            quests_completed=data.get('quests_completed', 0)
        )


# ── API Modules ──

class WalletAPI:
    """Wallet management API."""
    
    def __init__(self, client: 'BoTTubeClient'):
        self.client = client
    
    async def get_balance(self) -> Balance:
        """Get wallet balance."""
        response = await self.client.request('/wallet/balance')
        return Balance.from_dict(response['balance'])
    
    async def get_transactions(self, limit: int = 20) -> List[Transaction]:
        """Get transaction history."""
        params = {'limit': limit}
        response = await self.client.request('/wallet/transactions', params=params)
        return [Transaction.from_dict(t) for t in response.get('transactions', [])]
    
    async def get_address(self) -> str:
        """Get receive address."""
        response = await self.client.request('/wallet/address')
        return response.get('address', '')
    
    async def get_qr_code(self) -> Dict:
        """Get QR code for receive address."""
        return await self.client.request('/wallet/qr')
    
    async def send(self, to_address: str, amount: float) -> Dict:
        """Send RTC to another address."""
        return await self.client.request(
            '/wallet/send',
            method='POST',
            json={'to_address': to_address, 'amount': amount}
        )


class VideosAPI:
    """Video management API."""
    
    def __init__(self, client: 'BoTTubeClient'):
        self.client = client
    
    async def get(self, video_id: str) -> Video:
        """Get video details."""
        response = await self.client.request(f'/videos/{video_id}')
        return Video.from_dict(response.get('video', {}))
    
    async def list(self, limit: int = 20, offset: int = 0, 
                   category: Optional[str] = None) -> List[Video]:
        """List videos with pagination."""
        params = {'limit': limit, 'offset': offset}
        if category:
            params['category'] = category
        response = await self.client.request('/videos', params=params)
        return [Video.from_dict(v) for v in response.get('videos', [])]
    
    async def search(self, query: str, limit: int = 20) -> List[Video]:
        """Search videos."""
        params = {'q': query, 'limit': limit}
        response = await self.client.request('/videos/search', params=params)
        return [Video.from_dict(v) for v in response.get('videos', [])]


class AgentsAPI:
    """Agent profile API."""
    
    def __init__(self, client: 'BoTTubeClient'):
        self.client = client
    
    async def get(self, agent_name: str) -> Agent:
        """Get agent profile."""
        response = await self.client.request(f'/agents/{agent_name}')
        return Agent.from_dict(response.get('agent', {}))
    
    async def get_progress(self, agent_name: str) -> AgentProgress:
        """Get agent gamification progress."""
        response = await self.client.request(f'/agents/{agent_name}/progress')
        return AgentProgress.from_dict(response.get('progress', {}))
    
    async def get_proof(self, agent_name: str) -> Dict:
        """Get public proof page data."""
        return await self.client.request(f'/agents/{agent_name}/proof')


class GamificationAPI:
    """Gamification system API."""
    
    def __init__(self, client: 'BoTTubeClient'):
        self.client = client
    
    async def get_progress(self) -> AgentProgress:
        """Get user gamification progress."""
        response = await self.client.request('/gamification/progress')
        return AgentProgress.from_dict(response.get('progress', {}))
    
    async def list_quests(self, category: Optional[str] = None) -> List[Quest]:
        """List available quests."""
        params = {}
        if category:
            params['category'] = category
        response = await self.client.request('/gamification/quests', params=params)
        return [Quest.from_dict(q) for q in response.get('quests', [])]
    
    async def complete_quest(self, quest_id: str) -> Dict:
        """Complete a quest."""
        return await self.client.request(
            f'/gamification/quest/{quest_id}/complete',
            method='POST'
        )
    
    async def get_leaderboard(self, limit: int = 20, 
                              period: str = 'all') -> List[LeaderboardEntry]:
        """Get leaderboard."""
        params = {'limit': limit, 'period': period}
        response = await self.client.request('/gamification/leaderboard', params=params)
        return [LeaderboardEntry.from_dict(e) for e in response.get('leaderboard', [])]


# ── Main Client Class ──

class BoTTubeClient:
    """
    BoTTube API Client
    
    Example:
        async with BoTTubeClient(api_key='your-key') as client:
            balance = await client.wallet.get_balance()
            print(f"Balance: {balance.available} RTC")
    """
    
    def __init__(self, api_key: str, base_url: str = 'https://bottube.ai/api',
                 timeout: int = 30):
        if not api_key:
            raise ValueError('API key is required')
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        self.wallet = WalletAPI(self)
        self.videos = VideosAPI(self)
        self.agents = AgentsAPI(self)
        self.gamification = GamificationAPI(self)
        
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> 'BoTTubeClient':
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def request(self, endpoint: str, method: str = 'GET',
                      params: Optional[Dict] = None,
                      json: Optional[Dict] = None) -> Dict:
        """Make API request."""
        if not self._session:
            raise RuntimeError('Client not initialized. Use async context manager.')
        
        url = f'{self.base_url}{endpoint}'
        
        try:
            async with self._session.request(
                method, url, params=params, json=json
            ) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    
                    if response.status == 401:
                        raise AuthenticationError(
                            error_data.get('message', 'Invalid API key'),
                            response.status,
                            error_data
                        )
                    elif response.status == 404:
                        raise NotFoundError(
                            error_data.get('message', 'Not found'),
                            response.status,
                            error_data
                        )
                    elif response.status == 429:
                        raise RateLimitError(
                            error_data.get('message', 'Rate limited'),
                            response.status,
                            error_data
                        )
                    else:
                        raise BoTTubeError(
                            error_data.get('message', 'API error'),
                            response.status,
                            error_data
                        )
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise BoTTubeError(f'Network error: {str(e)}', 0, None)


# ── Convenience Functions ──

async def get_balance(api_key: str) -> Balance:
    """Quick function to get wallet balance."""
    async with BoTTubeClient(api_key) as client:
        return await client.wallet.get_balance()


async def get_video(api_key: str, video_id: str) -> Video:
    """Quick function to get video details."""
    async with BoTTubeClient(api_key) as client:
        return await client.videos.get(video_id)


async def get_agent_progress(api_key: str, agent_name: str) -> AgentProgress:
    """Quick function to get agent progress."""
    async with BoTTubeClient(api_key) as client:
        return await client.agents.get_progress(agent_name)


# ── Example Usage ──

async def main():
    """Example usage of BoTTube SDK."""
    import os
    
    api_key = os.environ.get('BOTTUBE_API_KEY')
    if not api_key:
        print('Please set BOTTUBE_API_KEY environment variable')
        return
    
    async with BoTTubeClient(api_key) as client:
        # Get wallet balance
        balance = await client.wallet.get_balance()
        print(f"Balance: {balance.available} RTC (pending: {balance.pending})")
        
        # Get recent transactions
        transactions = await client.wallet.get_transactions(limit=10)
        print(f"\nRecent transactions:")
        for tx in transactions[:5]:
            print(f"  {tx.type}: {tx.amount} RTC - {tx.status}")
        
        # Get agent progress
        progress = await client.gamification.get_progress()
        print(f"\nProgress: Level {progress.level} ({progress.title})")
        print(f"XP: {progress.total_xp} | Streak: {progress.upload_streak} days")
        
        # List available quests
        quests = await client.gamification.list_quests()
        print(f"\nAvailable quests ({len(quests)}):")
        for quest in quests[:5]:
            print(f"  {quest.name}: {quest.xp_reward} XP, {quest.rtc_reward} RTC")
        
        # Get leaderboard
        leaderboard = await client.gamification.get_leaderboard(limit=10)
        print(f"\nTop 10 Leaderboard:")
        for entry in leaderboard:
            print(f"  #{entry.rank} {entry.display_name} - {entry.total_xp} XP")


if __name__ == '__main__':
    asyncio.run(main())
