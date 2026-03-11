protocols segment-routing mpls mapping-server
---------------------------------------------

**Minimum user role:** operator

When the router is enabled as a mapping server, it maintains a mapping of prefixes and their SIDs. This is useful for allocating SIDs for Prefixes outside the segment-routing domain, for example prefixes of nodes in the IS-IS domain running only LDP and not segment-routing.

To enter the segment-routing mapping-server configuration hierarchy:

**Command syntax: mapping-server**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# mapping-server
    dnRouter(cfg-sr-mpls-mapping)#


**Removing Configuration**

To remove all mapping configuration:
::

    dnRouter(cfg-protocols-sr-mpls)# no mapping-server

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
