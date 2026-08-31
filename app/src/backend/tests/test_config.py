from pydantic import ValidationError

from src.backend.schemas.config import GlobalConfig


def test_expiry_days_default():
    cfg = GlobalConfig()
    assert cfg.expiry_days == 7


def test_expiry_days_explicit():
    cfg = GlobalConfig(expiry_days=14)
    assert cfg.expiry_days == 14


def test_expiry_days_missing_field_is_tolerated():
    # Field was added later; old configs without it must still parse.
    cfg = GlobalConfig(**{"delete_on_download": False, "output_dir": "/tmp/x"})
    assert cfg.expiry_days == 7


def test_expiry_days_rejects_non_int():
    try:
        GlobalConfig(expiry_days="seven")
    except ValidationError:
        return
    raise AssertionError("Expected ValidationError for non-int expiry_days")
