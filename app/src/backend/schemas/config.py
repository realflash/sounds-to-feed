from typing import List, Optional

from pydantic import BaseModel


class ProgrammeConfig(BaseModel):
    name: str
    start_from_date: Optional[str] = None
    display_name: Optional[str] = None


class GlobalConfig(BaseModel):
    delete_on_download: bool = True
    output_dir: str = "/data"


class AppConfig(BaseModel):
    global_config: GlobalConfig = GlobalConfig()
    programmes: List[ProgrammeConfig] = []
