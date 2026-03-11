network-services vrf instance protocols bgp bestpath deterministic-med
----------------------------------------------------------------------

**Minimum user role:** operator

When routes are advertised by different peers in the same autonomous system, you can instruct the BGP process to compare the MED variable to select the best path.

To enable this option:

**Command syntax: bestpath deterministic-med**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath deterministic-med


**Removing Configuration**

To disable this configuration:
::

    dnRouter(cfg-protocols-bgp)# no bestpath deterministic-med

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
