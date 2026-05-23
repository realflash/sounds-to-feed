from unittest.mock import MagicMock, patch

# Patch constructors before importing app
patch('src.backend.db.state.StateManager.__init__', return_value=None).start()
patch('src.backend.core.config_manager.ConfigManager.__init__', return_value=None).start()

from fastapi.testclient import TestClient  # noqa: E402

from src.backend.api.audio import get_config_manager as audio_get_config  # noqa: E402
from src.backend.api.audio import get_state_manager as audio_get_state  # noqa: E402
from src.backend.api.feed import get_config_manager as feed_get_config  # noqa: E402
from src.backend.api.feed import get_state_manager as feed_get_state  # noqa: E402
from src.backend.main import app  # noqa: E402

mock_state = MagicMock()
mock_config = MagicMock()

app.dependency_overrides[feed_get_state] = lambda: mock_state
app.dependency_overrides[audio_get_state] = lambda: mock_state
app.dependency_overrides[audio_get_config] = lambda: mock_config
app.dependency_overrides[feed_get_config] = lambda: mock_config

client = TestClient(app)

def test_feed_empty():
    from src.backend.schemas.config import AppConfig
    mock_config.get_config.return_value = AppConfig(programmes=[])
    mock_state.get_downloaded_episodes.return_value = []
    response = client.get("/feed.xml")
    assert response.status_code == 200
    assert b"Sounds to Feed" in response.content

def test_feed_display_name():
    from src.backend.schemas.config import AppConfig, ProgrammeConfig
    prog = ProgrammeConfig(name="Business Daily", display_name="Biz Daily Feed")
    mock_config.get_config.return_value = AppConfig(programmes=[prog])
    # The pid is testpid, the filename implies programme name 'Business Daily'
    mock_state.get_downloaded_episodes.return_value = [
        ("testpid", "/data/testpid_Business_Daily_ep.m4a")
    ]
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.stat') as mock_stat:
        
        # Mock stat for file size and mtime
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1234
        mock_stat_result.st_mtime = 1700000000
        mock_stat.return_value = mock_stat_result
        
        response = client.get("/feed.xml")
        assert response.status_code == 200
        # Title should use display_name "Biz Daily Feed" and episode "ep"
        assert b"<title>Biz Daily Feed: ep</title>" in response.content

def test_audio_not_found():
    mock_state.get_episode.return_value = None
    response = client.get("/audio/invalidpid")
    assert response.status_code == 404
        
def test_audio_not_downloaded():
    mock_state.get_episode.return_value = {'status': 'SERVED', 'filename': '/data/test.m4a'}
    response = client.get("/audio/servedpid")
    assert response.status_code == 404
