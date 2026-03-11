protocols bgp always-compare-med
--------------------------------

**Minimum user role:** operator

When two or more links exist between autonomous systems, the multi-exit discriminator (MED) values may be set to give preferences to certain routes. When comparing MED values, the lower value is preferred. By default, this function is disabled, and MED values are compared only if two paths have the same neighbor AS.

To configure the BGP process to always compare the MED metric on routes for best path selection, even when received from different ASs:

**Command syntax: always-compare-med**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# always-compare-med


**Removing Configuration**

To disable the always compare MED function:
::

    dnRouter(cfg-protocols-bgp)# no always-compare-med

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
