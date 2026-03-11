network-services vrf instance protocols bgp nexthop-trigger-delay
-----------------------------------------------------------------

**Minimum user role:** operator

If BGP reacts prematurely to IGP updates, traffic may be lost. This command allows you to set a delay in BGP's reaction to IGP updates when IGP convergence is slow.

You can change the delay interval for triggering next-hop calculations when a next-hop address tracking event occurs.

To set the delay:

**Command syntax: nexthop-trigger-delay [nexthop-trigger-delay]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Note**

- Setting the delay to 0 disables the delay.

**Parameter table**

+-----------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter             | Description                                                                      | Range | Default |
+=======================+==================================================================================+=======+=========+
| nexthop-trigger-delay | Change the delay interval that will trigger the scheduling of next-hop-tracking  | 0-100 | 5       |
|                       | feature                                                                          |       |         |
+-----------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# nexthop-trigger-delay 3


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp)# no nexthop-trigger-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+
