from dataclasses import dataclass
from typing import List, Dict, Tuple

@dataclass
class BgpRoute:
    community_index: int
    attr_index: int
    last_modified: int
    valid_route: bool
    reject_reason: str

@dataclass
class BgpAttrSet:
    index: int
    members: List[int]

RouteKey = tuple[str, str, int]  # (prefix, origin, path_id)
bgp_rib: dict[RouteKey, BgpRoute] = {}
bgp_attr_sets: Dict[int, BgpAttrSet] = {}