from pygnmi.client import gNMIclient, telemetryParser
from google.protobuf import json_format
from .processor import proc_attr_sets, process_routes
import threading
import logging
logger = logging.getLogger(__name__)

class gnmi_bgp_reader:
    def __init__(self, host, port, auth_user, auth_pass, insecure, vrf='default', afi="ipv4"):
        """
        Initialize the reader class. 
        Takes:
            - host: gNMI endpoint
            - port: gNMI endpoint's port
            - auth_user: username to authenticate with
            - auth_pass: password to authenticate with
            - insecure: whether to use insecure mode or not
            - vrf: VRF to pull routing information from
            - afi: address family to pull routing information for
        Telemetry is pulled using on_change mode, which syncs the entire RIB first, then only provides the updates.
        It should be noted this may be fairly taxing on both the collector and the router if there are a lot of routes.
        """

        self.host = host
        self.port = port
        self.auth_user = auth_user
        self.auth_pass = auth_pass
        self.insecure = insecure
        self.vrf = vrf
        logging.info(f"Using arguments: Host: {self.host}, Port:{self.port}, VRF: {self.vrf}, Insecure: {self.insecure}")
        # TODO: Add more AFIs
        if afi == "ipv4":
            self.afi = "IPV4_UNICAST"
        self.routes_path = f'/network-instances/network-instance[name={self.vrf}]/protocols/protocol[identifier=BGP][name=BGP]/bgp/rib/afi-safis/afi-safi[afi-safi-name={self.afi}]/ipv4-unicast/loc-rib/routes'
        self.attr_path = f'/network-instances/network-instance[name={self.vrf}]/protocols/protocol[identifier=BGP][name=BGP]/bgp/rib/attr-sets/attr-set/as-path'
        logging.debug(f"OpenConfig Routes Path: {self.routes_path}")
        logging.debug(f"OpenConfig Attributes Path: {self.attr_path}")
        self.subscribe_routes = {
            'subscription': [
                {
                    'path': self.routes_path,
                    'mode': 'on_change',
                }
            ],
            'use_aliases': False,
            'mode' : 'stream',
            'encoding': 'proto'
        }
        self.subscribe_attr = {
            'subscription': [
                {
                    'path': self.attr_path,
                    'mode': 'on_change',
                }
            ],
            'use_aliases': False,
            'mode' : 'stream',
            'encoding': 'proto'
        }

    def _route_update_loop(self):
        """
        Initiates collection of route metrics from the gNMI endpoint. 
        Processing is done in the `process_routes` function.
        """
        
        with gNMIclient(target= (self.host, self.port), 
                    username= self.auth_user, password = self.auth_pass, insecure=self.insecure) as gc:
            telementry_stream = gc.subscribe(subscribe=self.subscribe_routes)
            for telementry_entry in telementry_stream:
                telementry_entry = json_format.MessageToDict(telementry_entry, preserving_proto_field_name=True)
                process_routes(telementry_entry)

    def _attr_update_loop(self):
        """
        Initiates collection of attributes from the gNMI endpoint. 
        Processing is done in the `proc_attr_sets` function.
        """

        with gNMIclient(target= (self.host, self.port), 
                    username= self.auth_user, password = self.auth_pass, insecure=self.insecure) as gc:
            telementry_stream = gc.subscribe(subscribe=self.subscribe_attr)
            for telementry_entry in telementry_stream:
                telementry_entry = json_format.MessageToDict(telementry_entry, preserving_proto_field_name=True)
                proc_attr_sets(telementry_entry)

    def start(self):
        """
        Spawns threads to begin metric collection on the route and attribute paths. 
        """

        threads = [
            threading.Thread(target=self._route_update_loop, daemon=True),
            threading.Thread(target=self._attr_update_loop,  daemon=True),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()