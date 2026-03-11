network-services vrf instance protocols bgp bestpath aigp-ignore
----------------------------------------------------------------

**Minimum user role:** operator

By default, the best path selection algorithm considers the AIGP metric as a tie-breaker between paths, and prefers paths with the AIGP attribute over paths without it. This command forces the NCR to only consider the AIGP attribute in the best path algorithm if both paths have an AIGP attribute.

To set the NCR to ignore the AIGP metric in best path calculation:

**Command syntax: bestpath aigp-ignore**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Note**

- This configuration is applicable to the default VRF only.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-bgp)# bestpath aigp-ignore


**Removing Configuration**

To disable the configuration:
::

    dnRouter(cfg-bgp)# no bestpath aigp-ignore

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 7.0     | Command introduced |
+---------+--------------------+
