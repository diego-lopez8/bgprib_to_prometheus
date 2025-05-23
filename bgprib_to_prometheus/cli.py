import argparse
from .reader import gnmi_bgp_reader
from prometheus_client import start_http_server, REGISTRY, ProcessCollector
import logging

def main():
    """
    Entrypoint for bgprib_to_prometheus. 
    Collects arguments from the user, configures logging, starts Prometheus, and instantiates a 
    Reader class to begin collecting metrics from the target.
    """
    p = argparse.ArgumentParser(prog='OpenConfig BGP RIB over gNMI to Prometheus. Takes an endpoint which implements openconfig_bgp_rib exposed over gNMI, processes it and outputs to various prometheus metrics.')
    p.add_argument("--host", required=True, help="Host. Can be a DNS or IP. Specify the port with --port.")
    p.add_argument("--port", required=True, help="Port on the host which is the endpoint for gNMI.")
    p.add_argument("--username", required=True, help="Username to authenticate with.")
    p.add_argument("--password", required=True, help="Password to authenticate with.")
    # TODO: It should probably pull for all vrfs by default unless otherwise specified.
    p.add_argument("--vrf", required=True, help="VRF to pull routes from. ")
    p.add_argument("--insecure", required=True, type=bool, help="Whether to allow insecure mode. True or False.")
    p.add_argument("--prometheus-port", type=int, required=False, default=8000, help="Port to expose Prometheus metrics on. Default to TCP/8000.")
    # TODO: Should allow more AFIs
    p.add_argument("--afi", required=True, help="Address family to pull.")
    p.add_argument("--debug", default=False, action='store_true', help="Enable debug mode.")
    args = p.parse_args()
    level = logging.DEBUG if args.debug else logging.INFO
    datefmt = '%Y-%m-%dT%H:%M:%S'
    fmt    = '%(asctime)s.%(msecs)03d %(levelname)-5s [%(name)s] %(message)s'
    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
    )
    logging.info(f"Exposing metrics on port {args.prometheus_port}")
    start_http_server(args.prometheus_port)
    REGISTRY.register(ProcessCollector())
    reader = gnmi_bgp_reader(args.host, args.port, args.username, args.password, args.insecure, args.vrf, args.afi)
    reader.start()