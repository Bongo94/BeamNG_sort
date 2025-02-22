# mod_info.py
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from enum import Enum


class ModType(Enum):
    VEHICLE = "Vehicle"
    MAP = "Map"
    OTHER = "Other"


@dataclass
class ModInfo:
    name: str
    author: str
    type: ModType
    description: str
    preview_images: List[Tuple[str, bytes]]  # (image_name, image_data)
    additional_info: Dict