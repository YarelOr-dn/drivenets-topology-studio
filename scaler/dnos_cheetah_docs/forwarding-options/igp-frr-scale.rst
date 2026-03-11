forwarding-options igp-frr-scale
--------------------------------

**Minimum user role:** operator

With igp-frr-scale enabled, additional haredware resources will be used to pre-install alternate paths for connected next-hops at hardware level.
When there is a large scale of next-hops that differ by the imposed egress label yet share same neighbor address and egress interface, 
it is recommended to use igp-frr-scale so that fast-reroute time will be independent of next-hops scale for a given failure event (such as interface failure)
IGP routes include:
- isis/ospf unicast routes    - leveraging lfa/ti-lfa
- isis/ospf-sr mpls routes    - leveraging ti-lfa
- ldp mpls routes             - leveraging lfa/r-lfa or ldp to sr stithching
- SR-TE first SID route       - leveraging ti-lfa
- BGP route neighbor PIC protection - leveraging lfa/ti-lfa

To enable igp-frr-scale:

**Command syntax: igp-frr-scale [admin-state]**

**Command mode:** config

**Hierarchies**

- forwarding-options

**Note**
- Configuration is platform dependent for supporting harewares only
- Configuration is not traffic effecting

**Parameter table**

+-------------+---------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                   | Range        | Default  |
+=============+===============================================================+==============+==========+
| admin-state | Configure to use hardware acceleration for fast-reroute logic | | disabled   | disabled |
|             |                                                               | | enabled    |          |
+-------------+---------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# forwarding-options
    dnRouter(cfg-fwd_opts)# igp-frr-scale enabled


**Removing Configuration**

To revert to default behavior:
::

    dnRouter(cfg-fwd_opts)# no igp-frr-scale

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
