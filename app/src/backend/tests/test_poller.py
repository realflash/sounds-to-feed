from unittest.mock import AsyncMock, MagicMock, patch

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
        mock_process.wait = AsyncMock(return_value=0)
        
        mock_process.stdout.read = AsyncMock(return_value=b"b0123456|Test Prog|Test Ep|Desc|Date\n")
        
        async def mock_stderr_iter():
            yield b""
            return
            
        mock_process.stderr = mock_stderr_iter()
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
        mock_process.wait = AsyncMock(return_value=0)
        
        mock_process.stdout.read = AsyncMock(return_value=b"b0123456|Test Prog|Test Ep|Desc|Date\n")
        
        async def mock_stderr_iter():
            yield b""
            return
            
        mock_process.stderr = mock_stderr_iter()
        mock_exec.return_value = mock_process
        
        with patch.object(poller, '_download_episode') as mock_download:
            mock_state.get_episode.return_value = {'status': 'SERVED', 'filename': '/data/test.m4a'}
            
            await poller._poll_programme("Test")
            
            mock_download.assert_not_called()

@pytest.mark.anyio
async def test_poller_environment_variables():
    mock_config = MagicMock()
    mock_state = MagicMock()
    
    poller = Poller(mock_config, mock_state)
    
    with patch('src.backend.core.poller.asyncio.create_subprocess_exec') as mock_exec:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.wait = AsyncMock(return_value=0)
        
        mock_process.stdout.read = AsyncMock(return_value=b"b0123456|Test Prog|Test Ep|Desc|Date\n")
        
        async def mock_stderr_iter():
            yield b""
            return
            
        mock_process.stderr = mock_stderr_iter()
        mock_exec.return_value = mock_process
        
        with patch.object(poller, '_download_episode'):
            mock_state.get_episode.return_value = None
            await poller._poll_programme("Test")
            
            # The search command should have been called
            assert mock_exec.call_count == 1
            
            # Verify the env argument does not contain PERL_UNICODE="AS"
            call_kwargs = mock_exec.call_args.kwargs
            assert "env" in call_kwargs
            env = call_kwargs["env"]
            assert "PERL_UNICODE" not in env, "PERL_UNICODE should not be set"
            assert env.get("LC_ALL") == "C.UTF-8"
            assert env.get("LANG") == "C.UTF-8"
