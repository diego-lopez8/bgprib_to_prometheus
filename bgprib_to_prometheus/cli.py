import argparse
from .reader import gnmi_bgp_reader
from prometheus_client import start_http_server

def main():
    p = argparse.ArgumentParser(prog='BGP RIB To Prometheus')
    p.add_argument("--host", required=True)
    p.add_argument("--port", required=True)
    p.add_argument("--username", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--vrf", required=True)
    p.add_argument("--insecure", required=True, type=bool)
    p.add_argument("--afi", required=True)
    args = p.parse_args()
    reader = gnmi_bgp_reader(args.host, args.port, args.username, args.password, args.insecure, 8000, args.vrf, args.afi)
    reader.start()