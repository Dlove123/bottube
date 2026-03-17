"""
BoTTube Python SDK Test Suite
Comprehensive tests using pytest and pytest-asyncio
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from bottube import (
    BoTTubeClient,
    BoTTubeError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    Balance,
    Transaction,
    Video,
    Agent,
    AgentProgress,
    Quest,
    LeaderboardEntry,
    get_balance,
    get_video,
    get_agent_progress,
)


# ── Fixtures ──

@pytest.fixture
def api_key():
    return 'test-api-key-12345'


@pytest.fixture
def client(api_key):
    return BoTTubeClient(api_key=api_key, timeout=5)


@pytest.fixture
def mock_response():
    """Create mock API response."""
    def _mock_response(data, status=200):
        mock = AsyncMock()
        mock.status = status
        mock.json = AsyncMock(return_value=data)
        return mock
    return _mock_response


# ── Client Tests ──

class TestBoTTubeClient:
    """Tests for BoTTubeClient class."""
    
    def test_init_with_valid_key(self, api_key):
        """Should create client with valid API key."""
        client = BoTTubeClient(api_key=api_key)
        assert client.api_key == api_key
        assert client.base_url == 'https://bottube.ai/api'
        assert client.timeout == 30
    
    def test_init_without_key(self):
        """Should raise error without API key."""
        with pytest.raises(ValueError, match='API key is required'):
            BoTTubeClient(api_key='')
    
    def test_init_with_custom_url(self, api_key):
        """Should use custom base URL."""
        client = BoTTubeClient(
            api_key=api_key,
            base_url='https://custom.api.com'
        )
        assert client.base_url == 'https://custom.api.com'
    
    def test_init_with_custom_timeout(self, api_key):
        """Should use custom timeout."""
        client = BoTTubeClient(api_key=api_key, timeout=60)
        assert client.timeout == 60
    
    @pytest.mark.asyncio
    async def test_context_manager(self, api_key):
        """Should work as async context manager."""
        async with BoTTubeClient(api_key=api_key) as client:
            assert client._session is not None
        assert client._session.closed
    
    @pytest.mark.asyncio
    async def test_request_without_session(self, api_key):
        """Should raise error without initialized session."""
        client = BoTTubeClient(api_key=api_key)
        with pytest.raises(RuntimeError, match='not initialized'):
            await client.request('/test')


# ── Wallet API Tests ──

class TestWalletAPI:
    """Tests for WalletAPI class."""
    
    @pytest.mark.asyncio
    async def test_get_balance(self, client, mock_response):
        """Should return wallet balance."""
        mock_data = {
            'balance': {
                'available': 150.5,
                'pending': 25.0,
                'total': 175.5
            }
        }
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            balance = await client.wallet.get_balance()
            
            assert isinstance(balance, Balance)
            assert balance.available == 150.5
            assert balance.pending == 25.0
            assert balance.total == 175.5
    
    @pytest.mark.asyncio
    async def test_get_transactions(self, client, mock_response):
        """Should return transaction history."""
        mock_data = {
            'transactions': [
                {'id': 1, 'type': 'quest_reward', 'amount': 5, 'status': 'confirmed', 'completed_at': 1234567890},
                {'id': 2, 'type': 'send', 'amount': -10, 'status': 'confirmed', 'completed_at': 1234567891}
            ],
            'count': 2
        }
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            transactions = await client.wallet.get_transactions(limit=10)
            
            assert len(transactions) == 2
            assert isinstance(transactions[0], Transaction)
            assert transactions[0].amount == 5
    
    @pytest.mark.asyncio
    async def test_get_address(self, client, mock_response):
        """Should return receive address."""
        mock_data = {'address': 'RTC1234567890abcdef1234567890abcdef1234'}
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            address = await client.wallet.get_address()
            
            assert address.startswith('RTC')
            assert len(address) == 43
    
    @pytest.mark.asyncio
    async def test_send(self, client, mock_response):
        """Should send RTC to address."""
        mock_data = {'tx_hash': '0xabcdef123456', 'status': 'pending'}
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            result = await client.wallet.send('RTC...', 50)
            
            assert result['tx_hash'] == '0xabcdef123456'
            assert result['status'] == 'pending'


# ── Videos API Tests ──

class TestVideosAPI:
    """Tests for VideosAPI class."""
    
    @pytest.mark.asyncio
    async def test_get_video(self, client, mock_response):
        """Should return video details."""
        mock_data = {
            'video': {
                'video_id': 'test-123',
                'title': 'Test Video',
                'description': 'A test',
                'views': 1000,
                'likes': 50,
                'agent_id': 1,
                'agent_name': 'TestBot',
                'created_at': 1234567890
            }
        }
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            video = await client.videos.get('test-123')
            
            assert isinstance(video, Video)
            assert video.video_id == 'test-123'
            assert video.views == 1000
    
    @pytest.mark.asyncio
    async def test_list_videos(self, client, mock_response):
        """Should return video list."""
        mock_data = {
            'videos': [
                {'video_id': '1', 'title': 'Video 1', 'views': 100, 'likes': 10, 'agent_id': 1, 'agent_name': 'Bot1', 'created_at': 1234567890},
                {'video_id': '2', 'title': 'Video 2', 'views': 200, 'likes': 20, 'agent_id': 2, 'agent_name': 'Bot2', 'created_at': 1234567891}
            ],
            'count': 2
        }
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            videos = await client.videos.list(limit=20)
            
            assert len(videos) == 2
            assert videos[0].title == 'Video 1'
    
    @pytest.mark.asyncio
    async def test_search_videos(self, client, mock_response):
        """Should search videos."""
        mock_data = {
            'videos': [{'video_id': '1', 'title': 'RustChain Tutorial', 'views': 500, 'likes': 50, 'agent_id': 1, 'agent_name': 'Bot', 'created_at': 1234567890}],
            'count': 1
        }
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            videos = await client.videos.search('RustChain', limit=10)
            
            assert len(videos) == 1
            mock_req.assert_called_once()


# ── Agents API Tests ──

class TestAgentsAPI:
    """Tests for AgentsAPI class."""
    
    @pytest.mark.asyncio
    async def test_get_agent(self, client, mock_response):
        """Should return agent profile."""
        mock_data = {
            'agent': {
                'agent_id': 1,
                'agent_name': 'TestBot',
                'display_name': 'Test Bot',
                'follower_count': 500,
                'video_count': 25
            }
        }
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            agent = await client.agents.get('TestBot')
            
            assert isinstance(agent, Agent)
            assert agent.agent_name == 'TestBot'
            assert agent.follower_count == 500
    
    @pytest.mark.asyncio
    async def test_get_progress(self, client, mock_response):
        """Should return agent progress."""
        mock_data = {
            'progress': {
                'level': 5,
                'title': 'Skilled',
                'xp_progress': 75,
                'total_xp': 1500,
                'upload_streak': 7,
                'completed_quests': 15,
                'stats': {'video_count': 25, 'total_views': 10000}
            }
        }
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            progress = await client.agents.get_progress('TestBot')
            
            assert isinstance(progress, AgentProgress)
            assert progress.level == 5
            assert progress.upload_streak == 7


# ── Gamification API Tests ──

class TestGamificationAPI:
    """Tests for GamificationAPI class."""
    
    @pytest.mark.asyncio
    async def test_get_progress(self, client, mock_response):
        """Should return user progress."""
        mock_data = {
            'progress': {
                'level': 3,
                'title': 'Regular',
                'total_xp': 600,
                'completed_quests': 10,
                'upload_streak': 3,
                'xp_progress': 50,
                'stats': {}
            }
        }
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            progress = await client.gamification.get_progress()
            
            assert progress.level == 3
    
    @pytest.mark.asyncio
    async def test_list_quests(self, client, mock_response):
        """Should list quests."""
        mock_data = {
            'quests': [
                {'id': 'first_upload', 'name': 'First Upload', 'xp_reward': 100, 'rtc_reward': 5, 'category': 'onboarding'},
                {'id': 'streak_7', 'name': '7-Day Streak', 'xp_reward': 500, 'rtc_reward': 25, 'category': 'retention'}
            ],
            'count': 2
        }
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            quests = await client.gamification.list_quests()
            
            assert len(quests) == 2
            assert quests[0].xp_reward == 100
    
    @pytest.mark.asyncio
    async def test_complete_quest(self, client, mock_response):
        """Should complete quest."""
        mock_data = {'message': 'Quest completed! +100 XP, +5 RTC'}
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            result = await client.gamification.complete_quest('first_upload')
            
            assert 'completed' in result['message'].lower()
    
    @pytest.mark.asyncio
    async def test_get_leaderboard(self, client, mock_response):
        """Should return leaderboard."""
        mock_data = {
            'leaderboard': [
                {'rank': 1, 'agent_id': 1, 'agent_name': 'TopBot', 'display_name': 'Top Bot', 'total_xp': 5000, 'level': 8, 'title': 'Legend', 'quests_completed': 50},
                {'rank': 2, 'agent_id': 2, 'agent_name': 'SecondBot', 'display_name': 'Second Bot', 'total_xp': 4500, 'level': 7, 'title': 'Master', 'quests_completed': 45}
            ]
        }
        
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_data
            leaderboard = await client.gamification.get_leaderboard(limit=10)
            
            assert len(leaderboard) == 2
            assert leaderboard[0].rank == 1


# ── Error Tests ──

class TestErrors:
    """Tests for error classes."""
    
    def test_botube_error(self):
        """Should create BoTTubeError with status."""
        error = BoTTubeError('Test error', 400, {'code': 'TEST'})
        
        assert error.message == 'Test error'
        assert error.status == 400
        assert error.data == {'code': 'TEST'}
    
    def test_authentication_error(self):
        """Should create AuthenticationError."""
        error = AuthenticationError('Invalid key', 401)
        
        assert isinstance(error, BoTTubeError)
        assert error.status == 401
    
    def test_not_found_error(self):
        """Should create NotFoundError."""
        error = NotFoundError('Not found', 404)
        
        assert isinstance(error, BoTTubeError)
        assert error.status == 404
    
    def test_rate_limit_error(self):
        """Should create RateLimitError."""
        error = RateLimitError('Too many requests', 429)
        
        assert isinstance(error, BoTTubeError)
        assert error.status == 429


# ── Convenience Function Tests ──

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    @pytest.mark.asyncio
    async def test_get_balance(self, mock_response):
        """Should get balance with convenience function."""
        mock_data = {'balance': {'available': 100, 'pending': 0, 'total': 100}}
        
        with patch('bottube.BoTTubeClient') as MockClient:
            mock_client = AsyncMock()
            mock_client.wallet.get_balance = AsyncMock(return_value=Balance(100, 0, 100))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            MockClient.return_value = mock_client
            
            balance = await get_balance('test-key')
            
            assert balance.available == 100
    
    @pytest.mark.asyncio
    async def test_get_video(self, mock_response):
        """Should get video with convenience function."""
        video_data = {'video_id': '123', 'title': 'Test', 'description': '', 'views': 100, 'likes': 10, 'agent_id': 1, 'agent_name': 'Bot', 'created_at': 1234567890}
        
        with patch('bottube.BoTTubeClient') as MockClient:
            mock_client = AsyncMock()
            mock_client.videos.get = AsyncMock(return_value=Video.from_dict(video_data))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            MockClient.return_value = mock_client
            
            video = await get_video('test-key', '123')
            
            assert video.video_id == '123'


# ── Data Class Tests ──

class TestDataClasses:
    """Tests for data classes."""
    
    def test_balance_from_dict(self):
        """Should create Balance from dict."""
        data = {'available': 100.5, 'pending': 25.0, 'total': 125.5}
        balance = Balance.from_dict(data)
        
        assert balance.available == 100.5
        assert balance.total == 125.5
    
    def test_transaction_from_dict(self):
        """Should create Transaction from dict."""
        data = {
            'id': 1, 'type': 'quest_reward', 'amount': 5,
            'status': 'confirmed', 'completed_at': 1234567890,
            'quest_id': 'first_upload', 'quest_name': 'First Upload'
        }
        tx = Transaction.from_dict(data)
        
        assert tx.id == 1
        assert tx.quest_name == 'First Upload'
    
    def test_video_from_dict(self):
        """Should create Video from dict."""
        data = {
            'video_id': '123', 'title': 'Test', 'description': 'Desc',
            'views': 1000, 'likes': 50, 'agent_id': 1, 'agent_name': 'Bot',
            'created_at': 1234567890, 'thumbnail': 'thumb.jpg', 'duration_sec': 60
        }
        video = Video.from_dict(data)
        
        assert video.video_id == '123'
        assert video.thumbnail == 'thumb.jpg'
    
    def test_agent_from_dict(self):
        """Should create Agent from dict."""
        data = {
            'agent_id': 1, 'agent_name': 'TestBot', 'display_name': 'Test',
            'follower_count': 500, 'video_count': 25, 'bio': 'A bot', 'avatar': 'avatar.png'
        }
        agent = Agent.from_dict(data)
        
        assert agent.follower_count == 500
        assert agent.bio == 'A bot'


# ── Integration Tests ──

class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, client, mock_response):
        """Should complete full workflow."""
        # Mock all API calls
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = [
                {'balance': {'available': 100, 'pending': 0, 'total': 100}},
                {'transactions': [], 'count': 0},
                {'progress': {'level': 1, 'title': 'Newcomer', 'total_xp': 0, 'upload_streak': 0, 'completed_quests': 0, 'xp_progress': 0, 'stats': {}}}
            ]
            
            # Get balance
            balance = await client.wallet.get_balance()
            assert balance.available == 100
            
            # Get transactions
            txs = await client.wallet.get_transactions()
            assert len(txs) == 0
            
            # Get progress
            progress = await client.gamification.get_progress()
            assert progress.level == 1


# ── Run Tests ──

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
