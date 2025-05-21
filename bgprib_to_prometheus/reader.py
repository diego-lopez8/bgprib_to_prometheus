from pygnmi.client import gNMIclient
from google.protobuf import json_format
from .processor import process_update
import threading
from prometheus_client import start_http_server

class gnmi_bgp_reader:
    def __init__(self, host, port, auth_user, auth_pass, insecure, prometheus_port, vrf=None, afi="ipv4"):
        self.host = host
        self.port = port
        self.auth_user = auth_user
        self.auth_pass = auth_pass
        self.insecure = insecure
        self.prometheus_port = prometheus_port
        self.vrf = vrf
        # TODO: Add more AFIs
        if afi == "ipv4":
            self.afi = "IPV4_UNICAST"
        self.routes_path = f'/network-instances/network-instance[name={self.vrf}]/protocols/protocol[identifier=BGP][name=BGP]/bgp/rib/afi-safis/afi-safi[afi-safi-name=IPV4_UNICAST]/ipv4-unicast/loc-rib/routes'
        self.attr_path = f'/network-instances/network-instance[name={self.vrf}]/protocols/protocol[identifier=BGP][name=BGP]/bgp/rib/attr-sets/attr-set/as-path'
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
    def test_gnmi_connection(self):
        pass

    def _route_update_loop(self):
        with gNMIclient(target= (self.host, self.port), 
                    username= self.auth_user, password = self.auth_pass, insecure=self.insecure) as gc:
            telementry_stream = gc.subscribe(subscribe=self.subscribe_routes)
            for telementry_entry in telementry_stream:
                telementry_entry = json_format.MessageToDict(telementry_entry, preserving_proto_field_name=True)
                #print(telementry_entry)
                process_update(telementry_entry)


    def _attr_update_loop(self):
        pass

    def start(self):
        start_http_server(self.prometheus_port)
        threads = [
            threading.Thread(target=self._route_update_loop, daemon=True),
            #threading.Thread(target=self._attr_loop,  daemon=True),
        ]
        for t in threads:
            t.start()

        # 3) block forever (or until interrupted)
        for t in threads:
            t.join()