network-services vrf instance routing-options maximum-routes address-family
---------------------------------------------------------------------------

**Minimum user role:** operator

To configure  maximum number of routes for the address family that  should be allowed within the non default VRF network instance.
When the specified value is reached, no further prefixes should be installed into the system's RIB from this network instance 
In case warning-only is enabled new routes should still be installed. 

**Command syntax: maximum-routes address-family [address-family]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance routing-options

**Note**

- maximum is a mandatory config for a maximum-route address family

- Connected and Static routes are always installed by RIB regardless of maximum route limit. These routes are counted for limit enforcement

- Route installment limit apply for BGP and IGP routes may result in blackholing

- The defined maximum limit is enforce by BGP so that BGP will not accept more then maximum routes and thus will not advertise routes to peers reducing blackholing risk

**Parameter table**

+----------------+-----------------------------------------------------------------------------+----------+---------+
| Parameter      | Description                                                                 | Range    | Default |
+================+=============================================================================+==========+=========+
| address-family | Reference to the address family for which the route limit is being applied. | | IPV4   | \-      |
|                |                                                                             | | IPV6   |         |
+----------------+-----------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)# routing-options
    dnRouter(cfg-vrf-inst-routing-options)# maximum-routes address-family IPV4
    dnRouter(cfg-inst-routing-options-max-routes)#

    dnRouter(cfg-vrf-inst-routing-options)# maximum-routes address-family IPV6
    dnRouter(cfg-inst-routing-options-max-routes)#


**Removing Configuration**

To disable maximum route limit for a given address family:
::

    dnRouter(cfg-vrf-inst-routing-options)# no maximum-routes address-family IPV4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
