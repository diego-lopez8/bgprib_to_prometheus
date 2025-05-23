# OpenConfig BGP RIB To Prometheus

This Python module collects data from endpoints which implement the OpenConfig BGP RIB YANG model, processes routes and attribute sets from `loc-rib`, and outputs via Prometheus. The motivation of this program is so that we can visualize and see changes to the local rib, particularly with AS path, in real time on edge routers. 

# Usage

```
usage: OpenConfig BGP RIB over gNMI to Prometheus. Takes an endpoint which implements openconfig_bgp_rib exposed over gNMI, processes it and outputs to various prometheus metrics.
       [-h] --host HOST --port PORT --username USERNAME --password PASSWORD --vrf VRF --insecure INSECURE
       [--prometheus-port PROMETHEUS_PORT] --afi AFI [--debug]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           Host. Can be a DNS or IP. Specify the port with --port.
  --port PORT           Port on the host which is the endpoint for gNMI.
  --username USERNAME   Username to authenticate with.
  --password PASSWORD   Password to authenticate with.
  --vrf VRF             VRF to pull routes from.
  --insecure INSECURE   Whether to allow insecure mode. True or False.
  --prometheus-port PROMETHEUS_PORT
                        Port to expose Prometheus metrics on. Default to TCP/8000.
  --afi AFI             Address family to pull.
  --debug               Enable debug mode.
  ```

## Example:

```
python3 -m bgprib_to_prometheus --host <ENDPOINT> --username <USER> --password <PASSWORD> --port <PORT> --insecure False --vrf <MYVRF> --afi ipv4
```

Then, navigate to `localhost:8000` to see metrics.

# Validation

This has been tested with Arista EOS 4.31.2F. 

To validate, add the following configuration to your Arista Router:

```
management api gnmi
   transport grpc default
      vrf <YOUR VRF>
   provider eos-native
!
management api models
   provider bgp
      bgp-rib
         ipv4-unicast
   !
!
```

# Coming Features

- More AFIs
- Collect `loc-rib` for all VRFs by default
- Collect community index infomration
- Sample Grafana graphs