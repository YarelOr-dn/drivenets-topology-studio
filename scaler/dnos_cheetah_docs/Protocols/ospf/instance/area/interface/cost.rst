protocols ospf instance area interface cost
-------------------------------------------

**Minimum user role:** operator

Set link cost for the specified interface. The cost value is set to router-LSA’s metric field and is used for SPF calculation. When the area default-cost is configured, the interface default cost value equals the configured area default-cost.
To set the link cost:

**Command syntax: cost [cost]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**
- no command returns the cost to its default value.
- Default cost value for a specific interface bandwidth is calculated by :math:`\frac{reference - bandwidth}{interface - bandwidth}` where reference-bandwidth, interface-bandwidth units are Mbits/s. when area default-cost is configured, default cost values equals area default cost
- User can configure the cost for the interface regardless if the cost-mirroring is enabled or not. The cost configuration will take place in the following cases:
* OSPF cost-mirroring is disabled
* OSPF adjacency is not yet up.

**Parameter table**

+-----------+------------------------------------------------+---------+---------+
| Parameter | Description                                    | Range   | Default |
+===========+================================================+=========+=========+
| cost      | set interface cost for interface under an area | 1-65535 | \-      |
+-----------+------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# cost 12050


**Removing Configuration**

To return the cost to its default value:
::

    dnRouter(cfg-protocols-ospf-area)# interface ge100-2/1/1

::

    dnRouter(cfg-ospf-area-if)# no cost

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
