protocols isis instance interface address-family weight level level-1
---------------------------------------------------------------------

**Minimum user role:** operator

Set the interface weight to be used for the weighted ecmp forwarding.
For weight = if-bw, the interface weight is the ratio of the interface bandwidth to 1G.
To configure the weight for the interface address-family:

**Command syntax: weight level level-1 [weight]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface address-family

**Note**

- By default, the IS-IS weight is per the interface bandwidth.

**Parameter table**

+-----------+-------------------+-----------------------+---------+
| Parameter | Description       | Range                 | Default |
+===========+===================+=======================+=========+
| weight    | ISIS type level-1 | 1..4294967295 | if-bw | \-      |
+-----------+-------------------+-----------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# weight level level-1 20

    dnRouter(cfg-protocols-isis-inst)# interface bundle-4
    dnRouter(cfg-isis-inst-if)# level level-1-2
    dnRouter(cfg-isis-inst-if)# address-family ipv6-unicast
    dnRouter(cfg-inst-if-afi)# weight level level-1 15
    dnRouter(cfg-inst-if-afi)# weight level level-1 if-bw


**Removing Configuration**

To revert to the default weight for a specific routing level:
::

    dnRouter(cfg-inst-if-afi)# no weight level-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
