protocols isis instance address-family ipv4-unicast load-balancing
------------------------------------------------------------------

**Minimum user role:** operator

Enabled weighted ECMP in ISIS.
Each of the ECMP paths in the ISIS route solution will have weight matching the egress interface weight.
Traffic will be load balanced between the different paths per the path weight ratio.

**Command syntax: load-balancing [LB-Type]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast

**Note**

- The configuration is per IS-IS topology. The chosen load-balancing methond in ipv4-unicast will also apply for ipv6 routes if working as a single-topology.

**Parameter table**

+-----------+------------------------------------------+-----------------+---------+
| Parameter | Description                              | Range           | Default |
+===========+==========================================+=================+=========+
| LB-Type   | ISIS multiple path load balancing method | | ecmp          | ecmp    |
|           |                                          | | weight-ecmp   |         |
+-----------+------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# load-balancing weight-ecmp
    dnRouter(cfg-isis-inst-afi)# exit
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# load-balancing ecmp


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-isis-inst-afi)# no load-balancing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
