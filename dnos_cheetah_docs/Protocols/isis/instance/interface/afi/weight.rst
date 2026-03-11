protocols isis instance interface address-family weight
-------------------------------------------------------

**Minimum user role:** operator

Set the interface weight to be used for the weighted ecmp forwarding.
For weight = if-bw, the interface weight is the ratio of the interface bandwidth to 1G.
To configure the weight for the interface address-family:

**Command syntax: weight [weight]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface address-family

**Note**

- By default, the IS-IS weight is per the interface bandwidth.

**Parameter table**

+-----------+-------------+-----------------------+---------+
| Parameter | Description | Range                 | Default |
+===========+=============+=======================+=========+
| weight    | weight      | 1..4294967295 | if-bw | if-bw   |
+-----------+-------------+-----------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# weight 20

    dnRouter(cfg-protocols-isis-inst)# interface bundle-3
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# weight if-bw

    dnRouter(cfg-protocols-isis-inst)# interface bundle-4
    dnRouter(cfg-isis-inst-if)# level level-1-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# weight level level-1 15
    dnRouter(cfg-inst-if-afi)# weight level level-2 if-bw

    dnRouter(cfg-protocols-isis-inst)# interface bundle-5
    dnRouter(cfg-isis-inst-if)# level level-1-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# weight level level-1 15
    dnRouter(cfg-inst-if-afi)# weight 20


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-inst-fa-afi)# no weight 60

To revert to the default weight (when weight per level is not set):
::

    dnRouter(cfg-inst-if-afi)# no weight
    dnRouter(cfg-inst-if-afi)# no weight 15

To revert to the default weight for a specific routing level:
::

    dnRouter(cfg-inst-if-afi)# no weight level-2

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
