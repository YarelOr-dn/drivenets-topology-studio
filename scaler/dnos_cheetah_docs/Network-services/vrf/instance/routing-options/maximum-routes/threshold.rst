network-services vrf instance routing-options maximum-routes address-family threshold
-------------------------------------------------------------------------------------

**Minimum user role:** operator

Percent of route maximum limit for which an alarm should be generated when the threshold number of installed routes is crossed
To set threshold:

**Command syntax: threshold [threshold]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance routing-options maximum-routes address-family

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| threshold | A percentage (%) of maximum routes limit to give you advance notice about RIB    | 1-100 | 75      |
|           | route scale.                                                                     |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)# routing-options
    dnRouter(cfg-vrf-inst-routing-options)# maximum-routes address-family IPV4
    dnRouter(cfg-inst-routing-options-max-routes)# threshold 85


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-inst-routing-options-max-routes)# no threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
