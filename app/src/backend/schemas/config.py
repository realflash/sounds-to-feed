from typing import List, Optional

from pydantic import BaseModel


class ProgrammeConfig(BaseModel):
    name: str
    start_from_date: Optional[str] = None
    display_name: Optional[str] = None


class GlobalConfig(BaseModel):
    delete_on_download: bool = True
    output_dir: str = "/data"
    # EPIC-002: time-based expiry window (days) measured from first download.
    # `delete_on_download` is retained for config backwards-compatibility but is
    # no longer used; deletion is now driven solely by expiry (see core/expiry.py).
    expiry_days: int = 7


class AppConfig(BaseModel):
    global_config: GlobalConfig = GlobalConfig()
    programmes: List[ProgrammeConfig] = []
