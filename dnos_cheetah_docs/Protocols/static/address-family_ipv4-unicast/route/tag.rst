protocols static address-family ipv4-unicast route tag
------------------------------------------------------

**Minimum user role:** operator

Specify a tag value that can be used as a match for controlling static-route redistribution using route policies
Tag value may be signalled to network in IS-IS

**Command syntax: tag [tag]**

**Command mode:** config

**Hierarchies**

- protocols static address-family ipv4-unicast route
- network-services vrf instance protocols static address-family ipv4-unicast route

**Parameter table**

+-----------+---------------+--------------+---------+
| Parameter | Description   | Range        | Default |
+===========+===============+==============+=========+
| tag       | add route tag | 1-4294967295 | \-      |
+-----------+---------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv4-unicast
    dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.0/24
    dnRouter(cfg-static-ipv4-route)# tag 100


**Removing Configuration**

To remove tag:
::

    dnRouter(cfg-static-ipv4-route)# no tag

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
