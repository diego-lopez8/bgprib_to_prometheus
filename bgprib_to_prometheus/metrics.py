from prometheus_client import Gauge, Info, REGISTRY
from .models import BgpRoute, RouteKey, BgpAttrSet
from typing import List, Dict, Tuple

bgp_as_path_hop = Gauge(
    'bgp_as_path_hop',
    'AS path number per hop',
    ['attr_index','position']
)

route_valid_gauge = Gauge(
    'bgp_route_valid',
    'Whether BGP route is valid (1 = valid, 0 = invalid)',
    ['prefix', 'origin', 'path_id']
)

route_bestpath_gauge = Gauge(
    'bgp_route_is_bestpath',
    'Whether BGP route is valid (1 = BESTPATH, 0 = NOT BEST PATH)',
    ['prefix', 'origin', 'path_id']
)

route_last_modified_gauge = Gauge(
    'bgp_route_last_modified',
    'BGP Last Modified time',
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
    'Additional BGP route info',
    ['prefix', 'origin', 'path_id']
)

# is there a way to remove metrics only given one single label?
def update_as_path_metrics(attrset: BgpAttrSet):
    # remove the complete path for a metric given the attr index
    for mfamily in REGISTRY.collect():
        if mfamily.name == 'bgp_as_path_hop':
            for sample in mfamily.samples:
                labels = sample.labels
                if int(labels.get('attr_index')) == attrset.index:
                    pos = labels.get('position')
                    bgp_as_path_hop.remove(attrset.index, pos)
    for pos, asn in enumerate(attrset.members, start=1):
        bgp_as_path_hop.labels(attrset.index, str(pos)).set(asn)

def update_metrics(rk: RouteKey, route: BgpRoute):
    labels = {'prefix': rk[0], 'origin': rk[1], 'path_id': str(rk[2])}
    route_valid_gauge.labels(**labels).set(1 if route.valid_route else 0)
    route_attr_gauge.labels(**labels).set(route.attr_index)
    route_comm_gauge.labels(**labels).set(route.community_index)
    route_last_modified_gauge.labels(**labels).set(route.last_modified)
    route_bestpath_gauge.labels(**labels).set(0 if route.reject_reason else 1)
    route_info.labels(**labels).info({'reject_reason': route.reject_reason})

def remove_metrics(rk: RouteKey):
    prefix, origin, path_id = rk
    path_id = str(path_id)
    route_valid_gauge.remove(prefix, origin, path_id)
    route_attr_gauge.remove(prefix, origin, path_id)
    route_comm_gauge.remove(prefix, origin, path_id)
    route_info.remove(prefix, origin, path_id)