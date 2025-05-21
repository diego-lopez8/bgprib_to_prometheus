from .models import BgpRoute, RouteKey, bgp_rib
from .metrics import update_metrics, remove_metrics

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

                    # Figure out which field changed
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
                path = delete['elem']
                key_dict = path[0]['key']
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