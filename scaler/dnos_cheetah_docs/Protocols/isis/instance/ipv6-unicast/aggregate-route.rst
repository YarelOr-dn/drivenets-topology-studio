protocols isis instance address-family ipv6-unicast aggregate-route
-------------------------------------------------------------------

**Minimum user role:** operator

Summarization reduces the number of routing updates that are flooded across areas. Though IS-IS supports summarization, being a link-state routing protocol, the link-state database must be identical on all routers within the area, and so summarization within an area is not possible. Therefore, you configure the summarization on the L1/L2 device that does the redistribution. The summarizing node will create an aggregate route with a next-hop null 0 (discard) in the IS-IS routing table and advertise it when a more specific route exists in the matching IS-IS level.

To configure route summarization in the L1/L2 device:

**Command syntax: aggregate-route [ip-prefix]** level [level] summary-only

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast

**Parameter table**

+--------------+----------------------------------------------------------------------------------+---------------+-----------+
| Parameter    | Description                                                                      | Range         | Default   |
+==============+==================================================================================+===============+===========+
| ip-prefix    | The summary route that will be advertised when a more specific route exists in   | X:X::X:X/x    | \-        |
|              | the matching IS-IS level. The route must match the address-family.               |               |           |
+--------------+----------------------------------------------------------------------------------+---------------+-----------+
| level        | Specify the required level for which to inject the summary prefix. Default       | | level-1     | level-1-2 |
|              | behavior is to add to both levels                                                | | level-2     |           |
|              |                                                                                  | | level-1-2   |           |
+--------------+----------------------------------------------------------------------------------+---------------+-----------+
| summary-only | Advertise only the summary route and not the contributing individual routes.     | Boolean       | False     |
+--------------+----------------------------------------------------------------------------------+---------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# aggregate-route 3.3.0.0/16
    dnRouter(cfg-isis-inst-afi)# aggregate-route 4.4.0.0/16 level level-1
    dnRouter(cfg-isis-inst-afi)# aggregate-route 5.5.0.0/16 level level-2 summary-only
    dnRouter(cfg-isis-inst-afi)# aggregate-route 6.6.0.0/16 level level-1-2


**Removing Configuration**

To remove all summary-prefix entries:
::

    dnRouter(cfg-isis-inst-afi)# no aggregate-route

To remove a specific summary-prefix entry:
::

    dnRouter(cfg-isis-inst-afi)# no aggregate-route 3.3.0.0/16

To revert to the default level:
::

    dnRouter(cfg-isis-inst-afi)# no aggregate-route 4.4.0.0/16 level level-2

To revert to the default level and remove the summary-only setting:
::

    dnRouter(cfg-isis-inst-afi)# no aggregate-route 5.5.0.0/16 level level-2 summary-only

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+
