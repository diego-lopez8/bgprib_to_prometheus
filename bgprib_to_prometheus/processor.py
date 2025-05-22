from .models import BgpRoute, RouteKey, bgp_rib, BgpAttrSet, bgp_attr_sets
from .metrics import update_metrics, remove_metrics, update_as_path_metrics

def process_routes(telemetry_entry):
    # TODO: Handle deletions
    # TODO: add logging
    update = telemetry_entry.get('update', {})
    sync = telemetry_entry.get("sync_response")
    if sync:
        print("responses synced.")
    elif update:
        rk = ()
        update_action = update.get('update', [])
        # TODO: understand delete functionality
        delete_action = update.get('delete', [])
        # Check if attr-set is in the prefix. If it is, then this attr set applies to the entire message
        prefix_elems = update.get('prefix', []).get('elem', [])
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
                update_metrics(rk, bgp_rib[rk])
    else:
        # is there some other behavior?
        print(telemetry_entry)

def proc_attr_sets(telemetry_entry):
    """
    Process the attribute set gnmi subscription response
    input: gnmi streaming telemetry entry object, in dictionary form
    pulls attr index and as path sequence out of the message and outputs to prometheus 
    has 2 main control sequences, when attr index is present in the top level notification message, or 
    when its present in each individual update message as part of a larger message
    """
    update = telemetry_entry.get('update', {})
    sync = telemetry_entry.get("sync_response")
    if sync:
        print("responses synced.")
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
                        update_as_path_metrics(attrset)
    else:
        print(telemetry_entry)

# depreciated
def process_attr_sets(telemetry_entry):
    """
    """
    # telemetry_entry is the overall update from gnmi
    # find if the attr set is in the prefix or if its in the update
    # if its in the prefix, look for the update with the as path, any with that inherit the attr set from the prefix
    # if there is no attr set in the prefix, it is dependent on the update with the member
    update = telemetry_entry.get('update', {})
    sync = telemetry_entry.get("sync_response")
    if sync:
        print("responses synced.")
    if update:
        update_action = update.get('update', [])
        delete_action = update.get('delete', [])
        print(len(update['prefix']['elem']))
        if update_action:
            if len(update_action) == 4:
                attr_idx = update['prefix']['elem'][7]['key']['index']
                members = [elem['uint_val'] for elem in update_action[3]['val']['leaflist_val']['element']]
                attrset = BgpAttrSet(index=int(attr_idx), members=members)
                bgp_attr_sets[attr_idx] = attrset
                update_as_path_metrics(attrset)
            else:
                for update in update_action:
                    try:
                        attr_idx = update['path']['elem'][0]['key']['index']
                        if len(update['path']['elem']) >= 5 and update['path']['elem'][4]['name']== 'member':
                            members = [elem['uint_val'] for elem in update['val']['leaflist_val']['element']]
                            attrset = BgpAttrSet(index=int(attr_idx), members=members)
                            bgp_attr_sets[attr_idx] = attrset
                            update_as_path_metrics(attrset)
                        else:
                            pass
                    except KeyError:
                        print(telemetry_entry)
                        print("Malformed:" , update_action)
                        print(len(update_action))
        else:
            print(update)

# depreciated
def process_update(telemetry_entry):
    """
    """
    update = telemetry_entry.get('update', {})
    sync = telemetry_entry.get("sync_response")
    if sync:
        print("responses synced.")
    if update:
        update_action = update.get('update', [])
        delete_action = update.get('delete', [])
        if update_action:
            for update in update_action:
                try:
                    path = update['path']['elem']
                    key_dict = path[0]['key']
                    prefix = key_dict['prefix']
                    origin = key_dict['origin']
                    path_id = int(key_dict['path-id'])
                    rk = (prefix, origin, path_id)

                    action = path[1]['name']
                    if action == 'state':
                        field = path[2]['name']
                    else:
                        field = action

                    val = update['val']
                    # Retrieve or initialize the dataclass
                    route = bgp_rib.get(rk, BgpRoute(valid=False, community_index=0, attr_index=0, reject_reason=''))
                    # Apply the update
                    if field == 'valid-route':
                        route.valid = bool(val.get('bool_val', False))
                    elif field == 'attr-index':
                        route.attr_index = int(val.get('uint_val', 0))
                    elif field == 'community-index':
                        route.community_index = int(val.get('uint_val', 0))
                    elif field == 'reject-reason':
                        route.reject_reason = val.get('string_val', '')
                    # else: ignore other fields
                    # Save back & push to Prometheus
                    bgp_rib[rk] = route
                    update_metrics(rk, route)
                except KeyError:
                    pass
                    #print("Malformed:" , update_action)
        elif delete_action:
            for delete in delete_action:
                print("DELETE")
                key_dict = delete['elem'][0]['key']
                prefix = key_dict['prefix']
                origin = key_dict['origin']
                path_id = int(key_dict['path-id'])
                rk = (prefix, origin, path_id)
                # try this
                try:
                    del bgp_rib[rk]
                except KeyError:
                    print("Key not found: ", rk)
                remove_metrics(rk)
                print("deleted: ", rk)
        else:
            print("Unknown set:", update.keys())