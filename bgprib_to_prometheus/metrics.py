from prometheus_client import Gauge, Info
from .models import BgpRoute, RouteKey

route_valid_gauge = Gauge(
    'bgp_route_valid',
    'Whether BGP route is valid (1 = valid, 0 = invalid)',
    ['prefix', 'origin', 'path_id']
)
route_attr_gauge = Gauge(
    'bgp_route_attr_index',
    'BGP route attribute index',
    ['prefix', 'origin', 'path_id']
)
route_comm_gauge = Gauge(
    'bgp_route_community_index',
    'BGP route community index',
    ['prefix', 'origin', 'path_id']
)
route_info = Info(
    'bgp_route_info',
    'Additional BGP route info (reject_reason)',
    ['prefix', 'origin', 'path_id']
)

def update_metrics(rk: RouteKey, route: BgpRoute):
    labels = {'prefix': rk[0], 'origin': rk[1], 'path_id': str(rk[2])}
    route_valid_gauge.labels(**labels).set(1 if route.valid else 0)
    route_attr_gauge.labels(**labels).set(route.attr_index)
    route_comm_gauge.labels(**labels).set(route.community_index)
    route_info.labels(**labels).info({'reject_reason': route.reject_reason})

def remove_metrics(rk: RouteKey):
    prefix, origin, path_id = rk
    path_id = str(path_id)

    route_valid_gauge.remove(prefix, origin, path_id)
    route_attr_gauge.remove(prefix, origin, path_id)
    route_comm_gauge.remove(prefix, origin, path_id)
    route_info.remove(prefix, origin, path_id)