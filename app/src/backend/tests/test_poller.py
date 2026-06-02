from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backend.core.poller import Poller
from src.backend.schemas.config import ProgrammeConfig


@pytest.fixture
def mock_httpx_client():
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client

    # Mock search response
    mock_search_response = MagicMock()
    mock_search_response.raise_for_status = MagicMock()
    mock_search_response.json.return_value = {
        "data": [
            {
                "data": [
                    {"type": "playable_item", "container": {"id": "b0123456", "title": "Test Prog"}}
                ]
            }
        ]
    }

    # Mock episodes response
    mock_episodes_response = MagicMock()
    mock_episodes_response.raise_for_status = MagicMock()
    mock_episodes_response.json.return_value = {
        "data": [
            {
                "id": "ep123456",
                "titles": {"primary": "Test Ep", "secondary": "Test Ep Desc"},
                "release": {"date": "2026-05-01T00:00:00Z"},
            }
        ]
    }

    # Configure the client to return these based on url
    async def side_effect(url, **kwargs):
        if "search" in str(url):
            return mock_search_response
        elif "playable" in str(url):
            return mock_episodes_response

    mock_client.get.side_effect = side_effect
    return mock_client


@pytest.mark.anyio
async def test_poller_poll_programme(mock_httpx_client):
    mock_config = MagicMock()
    mock_state = MagicMock()

    poller = Poller(mock_config, mock_state)

    with patch("src.backend.core.poller.httpx.AsyncClient", return_value=mock_httpx_client):
        with patch.object(poller, "_download_episode") as mock_download:
            mock_state.get_episode.return_value = None

            await poller._poll_programme(ProgrammeConfig(name="Test Prog"))

            mock_download.assert_called_once_with("ep123456", "Test Prog", "Test Ep Desc")


@pytest.mark.anyio
async def test_poller_poll_programme_already_served(mock_httpx_client):
    mock_config = MagicMock()
    mock_state = MagicMock()

    poller = Poller(mock_config, mock_state)

    with patch("src.backend.core.poller.httpx.AsyncClient", return_value=mock_httpx_client):
        with patch.object(poller, "_download_episode") as mock_download:
            mock_state.get_episode.return_value = {"status": "SERVED", "filename": "/data/test.m4a"}

            await poller._poll_programme(ProgrammeConfig(name="Test Prog"))

            mock_download.assert_not_called()


@pytest.mark.anyio
async def test_poller_download_episode():
    # Keep one test for the subprocess part in _download_episode
    mock_config = MagicMock()
    mock_state = MagicMock()

    poller = Poller(mock_config, mock_state)

    with patch("src.backend.core.poller.asyncio.create_subprocess_exec") as mock_exec:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.wait = AsyncMock(return_value=0)

        async def mock_stream_iter():
            yield b""
            return

        mock_process.stdout = mock_stream_iter()
        mock_process.stderr = mock_stream_iter()
        mock_exec.return_value = mock_process

        with patch("src.backend.core.poller.Path.exists", return_value=True):
            await poller._download_episode("ep123", "Test", "TestEp")

            # The download command should have been called
            assert mock_exec.call_count == 1

            call_kwargs = mock_exec.call_args.kwargs
            assert "env" in call_kwargs
            env = call_kwargs["env"]
            assert "PERL_UNICODE" not in env, "PERL_UNICODE should not be set"
            assert env.get("LC_ALL") == "C.UTF-8"
            assert env.get("LANG") == "C.UTF-8"
