protocols segment-routing mpls policy destination flex-algo
-----------------------------------------------------------

**Minimum user role:** operator

The destination is the last hop (tail-end) of the segment-routing policy and is a mandatory configuration. 
The configuration is much like the hop configuration (see "segment-routing mpls path segment-list hop"), except that it marks the last hop.
Flex-algo defines in which Flex-Algo topology the requested destination SID should be matched.

To configure the policy's destination for the Flex-Algo SID:


**Command syntax: destination [destination ip-address] flex-algo [flex-algo id]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Parameter table**

+------------------------+--------------------------------------------------------------+--------------+---------+
| Parameter              | Description                                                  | Range        | Default |
+========================+==============================================================+==============+=========+
| destination ip-address | segment-routing policy destination                           | | A.B.C.D    | \-      |
|                        |                                                              | | X:X::X:X   |         |
+------------------------+--------------------------------------------------------------+--------------+---------+
| flex-algo id           | segment-routing policy destination flex-algorithm identifier | 128-255      | \-      |
+------------------------+--------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR-POLICY_1
    dnRouter(cfg-sr-mpls-policy)# destination 1.1.1.1 flex-algo 130

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR-_v6_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# destination 1717:1717::1 flex-algo 130


**Removing Configuration**

To remove destination configuration:
::

    dnRouter(cfg-sr-mpls-policy)# no destination

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
| 18.2    | Add ipv6 support   |
+---------+--------------------+
