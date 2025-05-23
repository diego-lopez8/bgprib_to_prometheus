from .models import BgpRoute, RouteKey, bgp_rib, BgpAttrSet, bgp_attr_sets
from .metrics import update_metrics, remove_metrics, update_as_path_metrics
import logging
logger = logging.getLogger(__name__)

def process_routes(telemetry_entry):
    """
    Function to process route telemetry collected over gNMI, and outputs via Prometheus. 
    Format:
        Routes are uniquely identified by a key of (prefix, path-id, origin). 
        This key is present in the `route` container, which may either be present in the prefix or path of the notification.
        If the notification only contains one key (only one update), then the key will typically be present in the prefix for the notification
        itself. If there are multiple keys in he update, the key will not be present in the prefix, and will be present
        in each update's individual path.
    The gNMI endpoint may specify to update or delete a route key. Depending on this, the key is added or removed 
    from Prometheus monitoring.
    """
    # TODO: Handle deletions
    # TODO: add logging
    update = telemetry_entry.get('update', {})
    sync = telemetry_entry.get("sync_response", {})
    if sync:
        logging.info(f"Routes Synced. Total number of route keys: {len(bgp_rib)}")
    elif update:
        rk = ()
        update_action = update.get('update', [])
        # TODO: understand delete functionality
        delete_action = update.get('delete', [])
        # Check if attr-set is in the prefix. If it is, then this attr set applies to the entire message
        prefix_elems = update.get('prefix', []).get('elem', [])
        # if there is an update action
        if update_action:
            for prefix_elem in prefix_elems:
                if prefix_elem.get('name', []) == "route":
                    prefix = prefix_elem.get('key', []).get('prefix', [])
                    origin = prefix_elem.get('key', []).get('origin', [])
                    path_id = int(prefix_elem.get('key', []).get('path-id', []))
                    rk = (prefix, origin, path_id)
            if rk:
                # route unique ID was present in the prefix of the update, so all parts of this update belong to the route
                route = bgp_rib.setdefault(
                    rk,
                    BgpRoute(community_index=0, attr_index=0, last_modified=0, valid_route=False, reject_reason="")
                )
                for update_elem in update_action:
                    path_elements = update_elem.get('path', []).get('elem', [])
                    for path_element in path_elements:
                        if path_element.get('name', []) == "attr-index":
                            route.attr_index = update_elem.get('val', []).get('uint_val', [])
                        if path_element.get('name', []) == "community-index":
                            route.community_index = update_elem.get('val', []).get('uint_val', [])
                        if path_element.get('name', []) == "last-modified":
                            route.last_modified = update_elem.get('val', []).get('uint_val', [])
                        if path_element.get('name', []) == "valid-route":
                            route.valid_route = update_elem.get('val', []).get('bool_val', [])
                        if path_element.get('name', []) == "reject-reason":
                            route.reject_reason = update_elem.get('val', []).get('string_val', [])
                bgp_rib[rk] = route
                logging.debug(f"UPDATE Route Metrics for: {bgp_rib[rk]}")
                update_metrics(rk, bgp_rib[rk])
            
            else:
                rks_modified = []
                for update_elem in update_action:
                    path_elements = update_elem.get('path', []).get('elem', [])
                    rk = ()
                    for path_element in path_elements:
                        if path_element.get('name', []) == "route":
                            prefix = path_element.get('key', []).get('prefix', [])
                            origin = path_element.get('key', []).get('origin', [])
                            path_id = int(path_element.get('key', []).get('path-id', []))
                            rk = (prefix, origin, path_id)
                            if rk not in rks_modified:
                                rks_modified.append(rk)
                    route = bgp_rib.setdefault(
                        rk,
                        BgpRoute(community_index=0, attr_index=0, last_modified=0, valid_route=False, reject_reason="")
                    )
                    for path_element in path_elements:
                        if path_element.get('name', []) == "attr-index":
                            route.attr_index = update_elem.get('val', []).get('uint_val', [])
                        if path_element.get('name', []) == "community-index":
                            route.community_index = update_elem.get('val', []).get('uint_val', [])
                        if path_element.get('name', []) == "last-modified":
                            route.last_modified = update_elem.get('val', []).get('uint_val', [])
                        if path_element.get('name', []) == "valid-route":
                            route.valid_route = update_elem.get('val', []).get('bool_val', [])
                        if path_element.get('name', []) == "reject-reason":
                            route.reject_reason = update_elem.get('val', []).get('string_val', [])
                    if rk not in rks_modified:
                        rks_modified.append(rk)
                for rk in rks_modified:
                    logging.debug(f"UPDATE Route Metrics for: {bgp_rib[rk]}")
                    update_metrics(rk, bgp_rib[rk])
        elif delete_action:
            # only one delete per update...?
            for delete_update in delete_action:
                delete_elem = delete_update.get('elem', [])
                for elem in delete_elem:
                    if elem.get('name', "") == "route":
                        prefix = elem.get("key", {}).get("prefix", "")
                        origin = elem.get("key", {}).get("origin", "")
                        path_id = elem.get("key", {}).get("path-id", "")
                        rk = (prefix, origin, path_id)
                        if rk in bgp_rib:
                            logging.debug(f"DELETE Route Metrics for: {bgp_rib[rk]}")
                            remove_metrics(rk)
                            bgp_rib.pop(rk, None)
        else:
            logging.info(f"Unhandled Route entry, no inner delete or update action: {telemetry_entry}")
    else:
        # is there some other behavior?
        logging.info(f"Unhandled Route entry: {telemetry_entry}")


def proc_attr_sets(telemetry_entry):
    """
    Function to process attribute telemetry collected over gNMI, and outputs via Prometheus. 
    Format:
        Attributes are unqiuely identified by the attribute index value. 
        This key is present in the `attr-set` container, which may either be present in the prefix or path of the notification.
        If the notification only contains one attr-set (only one update), then the key will typically be present in the prefix for the notification
        itself. If there are multiple attr-sets in he update, the attr-set will not be present in the prefix, and will be present
        in each update's individual path.
    The gNMI endpoint may specify to update or delete a attr-set. Depending on this, the key is added or removed 
    from Prometheus monitoring.
    """
    update = telemetry_entry.get('update', {})
    sync = telemetry_entry.get("sync_response", {})
    if sync:
        logging.info(f"Attributes Synced. Total number of route keys: {len(bgp_attr_sets)}")
    elif update:
        attr_idx = ''
        update_action = update.get('update', [])
        # TODO: understand delete functionality
        delete_action = update.get('delete', [])
        # Check if attr-set is in the prefix. If it is, then this attr set applies to the entire message
        prefix_elems = update.get('prefix', []).get('elem', [])
        for elem in prefix_elems:
            if elem.get('name') == "attr-set":
                attr_idx = elem.get('key', {}).get("index", '')
        if attr_idx:
            # attr_index was present in the top level prefix, so this entire message can be treated as belonging to this attr_index
            for update_elem in update_action:
                path_elements = update_elem.get('path', []).get('elem', [])
                for path_element in path_elements:
                    if path_element.get('name', []) == "member":
                        members_dict_list = update_elem.get('val', []).get('leaflist_val', []).get('element', [])
                        members = [member_dict['uint_val'] for member_dict in members_dict_list]
                        attrset = BgpAttrSet(index=int(attr_idx), members=members)
                        bgp_attr_sets[attr_idx] = attrset
                        logging.debug(f"UPDATE Attrset Metrics for: {attrset}")
                        update_as_path_metrics(attrset)
        else:
            # attr_index was not present in the top level prefix, so each update message may have a differring attr_index
            for update_elem in update_action:
                path_elements = update_elem.get('path', []).get('elem', [])
                for path_element in path_elements:
                    if path_element.get('name', []) == "attr-set":
                        attr_idx = path_element.get('key', []).get('index', [])
                    if path_element.get('name', []) == "member":
                        members_dict_list = update_elem.get('val', []).get('leaflist_val', []).get('element', [])
                        members = [member_dict['uint_val'] for member_dict in members_dict_list]
                        attrset = BgpAttrSet(index=int(attr_idx), members=members)
                        # do we need this?
                        bgp_attr_sets[attr_idx] = attrset
                        logging.debug(f"UPDATE Attrset Metrics for: {attrset}")
                        update_as_path_metrics(attrset)
    else:
        logging.info(f"Unhandled Attribute entry: {telemetry_entry}")