protocols isis instance forwarding-adjacency address-family
-----------------------------------------------------------

**Minimum user role:** operator

Use this command to enable forwarding adjacency for a specific address family. For ipv4-unicast, a forwarding-adjacency link will be added to the default IS-IS topology (topology #0). You must configure at least one address-family to enable forwarding-adjacency for the relevant topology.

To enable forwarding adjacency for a specific address family:

**Command syntax: address-family [address-family]**

**Command mode:** config

**Hierarchies**

- protocols isis instance forwarding-adjacency

**Note**

- There is no default address-family.

**Parameter table**

+----------------+-----------------------------------------------------------------------+--------------+---------+
| Parameter      | Description                                                           | Range        | Default |
+================+=======================================================================+==============+=========+
| address-family | The address-family (AFI-SAFI) on which to enable forwarding adjacency | ipv4-unicast | \-      |
+----------------+-----------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# forwarding-adjacency TUNNEL_1
    dnRouter(cfg-isis-inst-fa)# address-family ipv4-unicast
    dnRouter(cfg-inst-fa-afi)#


**Removing Configuration**

To remove the address-family configuration:
::

    dnRouter(cfg-isis-inst-fa)# no address-family ipv4-unicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2    | Command introduced |
+---------+--------------------+
