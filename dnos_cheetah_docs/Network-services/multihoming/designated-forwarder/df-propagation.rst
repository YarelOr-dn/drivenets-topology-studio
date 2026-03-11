network-services multihoming designated-forwarder df-propagation
----------------------------------------------------------------

**Minimum user role:** operator

Set whether df-propagation shall be enabled or disabled. 
When enabled, if this PE is not the DF then LACP signals OOS to the CE.

**Command syntax: df-propagation [df-propagation]**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Parameter table**

+----------------+------------------------------------------------------------------+------------+----------+
| Parameter      | Description                                                      | Range      | Default  |
+================+==================================================================+============+==========+
| df-propagation | Whether non-DF should be propagated to CE using LACP out-of-sync | enabled    | disabled |
|                |                                                                  | disabled   |          |
+----------------+------------------------------------------------------------------+------------+----------+

**Example**
::

    dev-dnRouter#
    dev-dnRouter# configure
    dev-dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# designated-forwarder
    dnRouter(cfg-mh-int-df)# df-propagation enabled
    dnRouter(cfg-mh-int-df)#


**Removing Configuration**

To revert the df-propagation configuration to its default of disabled.
::

    dnRouter(cfg-mh-int-df)# no df-propagation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
