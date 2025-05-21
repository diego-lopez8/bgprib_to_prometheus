from dataclasses import dataclass

@dataclass
class BgpRoute:
    valid: bool
    community_index: int
    attr_index: int
    reject_reason: str

RouteKey = tuple[str, str, int]  # (prefix, origin, path_id)
bgp_rib: dict[RouteKey, BgpRoute] = {}