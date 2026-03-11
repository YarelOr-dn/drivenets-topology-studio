network-services vrf instance protocols bgp network import-check
----------------------------------------------------------------

**Minimum user role:** operator

This command instructs the BGP process to validate that the BGP route exists in the routing table (RIB) before injecting it into BGP and advertising it to the BGP neighbors.

**Command syntax: network import-check [network-import-check]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Parameter table**

+----------------------+---------------------------------------+--------------+---------+
| Parameter            | Description                           | Range        | Default |
+======================+=======================================+==============+=========+
| network-import-check | Check BGP network route exists in IGP | | enabled    | enabled |
|                      |                                       | | disabled   |         |
+----------------------+---------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# network import-check disabled


**Removing Configuration**

To revert to the default configuration:
::

    dnRouter(cfg-protocols-bgp)# no network import-check

**Command History**

+---------+--------------------------------------------+
| Release | Modification                               |
+=========+============================================+
| 6.0     | Command introduced                         |
+---------+--------------------------------------------+
| 9.0     | Added Enabled/Disabled value to the syntax |
+---------+--------------------------------------------+
