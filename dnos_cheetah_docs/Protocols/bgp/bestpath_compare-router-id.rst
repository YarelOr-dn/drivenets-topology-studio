protocols bgp bestpath compare-router-id
----------------------------------------

**Minimum user role:** operator

When comparing routes, if all metric stages 1-10 are equal, including local preference, AS-path length, IGP cost, and MED, BGP can select the best path based on router-id (stage 11). This command causes BGP to prefer the route with the lower router-id when all other metrics are equal.

To enable this function:

**Command syntax: bestpath compare-router-id**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- If the route contains route reflector attributes, BGP will use the ORIGINATOR_ID as the ROUTER_ID for comparison. Otherwise, the router-id of the neighbor from which the route was received is used.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath compare-router-id


**Removing Configuration**

To disable the compare-router-id option:
::

    dnRouter(cfg-protocols-bgp)# no bestpath compare-router-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
