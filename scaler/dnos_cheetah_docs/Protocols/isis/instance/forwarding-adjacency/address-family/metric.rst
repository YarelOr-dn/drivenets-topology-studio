protocols isis instance forwarding-adjacency address-family metric
------------------------------------------------------------------

**Minimum user role:** operator

To configure the forwarding-adjacency link metric in the relevant topology:

**Command syntax: metric [metric]**

**Command mode:** config

**Hierarchies**

- protocols isis instance forwarding-adjacency address-family

**Parameter table**

+-----------+---------------------------------------------------------+------------+---------+
| Parameter | Description                                             | Range      | Default |
+===========+=========================================================+============+=========+
| metric    | The metric value to be set for the forwarding-adjacency | 1-16777215 | 10      |
+-----------+---------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# forwarding-adjacency TUNNEL_1
    dnRouter(cfg-isis-inst-fa)# address-family ipv4-unicast
    dnRouter(cfg-inst-fa-afi)# metric 60


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-inst-fa-afi)# no metric 60

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2    | Command introduced |
+---------+--------------------+
