from unittest.mock import MagicMock, patch

import pytest

from src.backend.core.poller import Poller


@pytest.mark.anyio
async def test_poller_poll_programme():
    mock_config = MagicMock()
    mock_state = MagicMock()
    
    poller = Poller(mock_config, mock_state)
    
    with patch('src.backend.core.poller.asyncio.create_subprocess_exec') as mock_exec:
        mock_process = MagicMock()
        mock_process.returncode = 0
        
        async def mock_communicate():
            return b"b0123456|Test Prog|Test Ep|Desc|Date\n", b""
            
        mock_process.communicate = mock_communicate
        mock_exec.return_value = mock_process
        
        with patch.object(poller, '_download_episode') as mock_download:
            mock_state.get_episode.return_value = None
            
            await poller._poll_programme("Test")
            
            mock_download.assert_called_once_with("b0123456", "Test Prog", "Test Ep")

@pytest.mark.anyio
async def test_poller_poll_programme_already_served():
    mock_config = MagicMock()
    mock_state = MagicMock()
    
    poller = Poller(mock_config, mock_state)
    
    with patch('src.backend.core.poller.asyncio.create_subprocess_exec') as mock_exec:
        mock_process = MagicMock()
        mock_process.returncode = 0
        
        async def mock_communicate():
            return b"b0123456|Test Prog|Test Ep|Desc|Date\n", b""
            
        mock_process.communicate = mock_communicate
        mock_exec.return_value = mock_process
        
        with patch.object(poller, '_download_episode') as mock_download:
            mock_state.get_episode.return_value = {'status': 'SERVED', 'filename': '/data/test.m4a'}
            
            await poller._poll_programme("Test")
            
            mock_download.assert_not_called()
