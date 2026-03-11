routing-options table mpls-nh-ipv6
----------------------------------

**Minimum user role:** operator

To enter the mpls-nh-ipv6 routing table configuration level:


**Command syntax: table mpls-nh-ipv6**

**Command mode:** config

**Hierarchies**

- routing-options

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# table mpls-nh-ipv6
    dnRouter(cfg-routing-option-mpls-nh-ipv6)#


**Removing Configuration**

To revert all table configurations to default:
::

    dnRouter(cfg-routing-option)# no table mpls-nh-ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
