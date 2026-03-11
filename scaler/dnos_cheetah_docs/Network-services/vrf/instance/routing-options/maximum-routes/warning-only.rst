network-services vrf instance routing-options maximum-routes address-family warning-only
----------------------------------------------------------------------------------------

**Minimum user role:** operator

When enabled, the route limit specified is considered only as a warning - and routes should continue to be installed into the
RIB over the limit specified in the maximum leaf.
To set warning-only:

**Command syntax: warning-only [warning-only]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance routing-options maximum-routes address-family

**Parameter table**

+--------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter    | Description                                                                      | Range        | Default  |
+==============+==================================================================================+==============+==========+
| warning-only | When enabled, the route limit specified is considered only as a warning - and    | | enabled    | disabled |
|              | routes should continue to be installed into the RIB over the limit specified in  | | disabled   |          |
|              | the maximum leaf.                                                                |              |          |
+--------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)# routing-options
    dnRouter(cfg-vrf-inst-routing-options)# maximum-routes address-family IPV4
    dnRouter(cfg-inst-routing-options-max-routes)# warning-only enabled


**Removing Configuration**

To revert behavior to default:
::

    dnRouter(cfg-inst-routing-options-max-routes)# no warning-only

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
