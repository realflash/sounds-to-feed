from unittest.mock import MagicMock, patch

# Patch constructors before importing app
patch('src.backend.db.state.StateManager.__init__', return_value=None).start()
patch('src.backend.core.config_manager.ConfigManager.__init__', return_value=None).start()

from fastapi.testclient import TestClient  # noqa: E402

from src.backend.api.audio import get_config_manager as audio_get_config  # noqa: E402
from src.backend.api.audio import get_state_manager as audio_get_state  # noqa: E402
from src.backend.api.feed import get_state_manager as feed_get_state  # noqa: E402
from src.backend.main import app  # noqa: E402

mock_state = MagicMock()
mock_config = MagicMock()

app.dependency_overrides[feed_get_state] = lambda: mock_state
app.dependency_overrides[audio_get_state] = lambda: mock_state
app.dependency_overrides[audio_get_config] = lambda: mock_config

client = TestClient(app)

def test_feed_empty():
    mock_state.get_downloaded_episodes.return_value = []
    response = client.get("/feed.xml")
    assert response.status_code == 200
    assert b"Sounds to Feed" in response.content

def test_audio_not_found():
    mock_state.get_episode.return_value = None
    response = client.get("/audio/invalidpid")
    assert response.status_code == 404
        
def test_audio_not_downloaded():
    mock_state.get_episode.return_value = {'status': 'SERVED', 'filename': '/data/test.m4a'}
    response = client.get("/audio/servedpid")
    assert response.status_code == 404
