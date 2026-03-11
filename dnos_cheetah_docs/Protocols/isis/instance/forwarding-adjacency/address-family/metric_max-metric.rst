protocols isis instance forwarding-adjacency address-family metric max-metric
-----------------------------------------------------------------------------

**Minimum user role:** operator

This command sets the forwarding-adjacency link metric to be the configured max-metric value in \"isis max-metric\". When disabled, the configured metric value will be used for the link.

To set 'max-metric' as the metric value for the forwarding-adjacency link:

**Command syntax: metric max-metric**

**Command mode:** config

**Hierarchies**

- protocols isis instance forwarding-adjacency address-family

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# forwarding-adjacency TUNNEL_2
    dnRouter(cfg-isis-inst-fa)# address-family ipv4-unicast
    dnRouter(cfg-inst-fa-afi)# metric max-metric


**Removing Configuration**

To revert the metric to the configured metric value:
::

    dnRouter(cfg-inst-fa-afi)# no metric max-metric

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2    | Command introduced |
+---------+--------------------+
