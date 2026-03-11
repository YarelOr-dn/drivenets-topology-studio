network-services vrf instance protocols bgp route-reflection policy-out attribute-change
----------------------------------------------------------------------------------------

**Minimum user role:** operator

Support modification of the following BGP path attributes by the policy out when acting as a Route-reflector:

NEXT_HOP
AS_PATH
LOCAL_PREF
MED

By default, per RFC4456#10, when acting as a Route-Reflector, for iBGP advertisement, DNOS will not apply any modification for the attributes provided above if the path is an iBGP path. Even if it was explicitly required by the neighbor policy out.
By default, per RFC4456#10, when acting as a Route-Reflector for iBGP advertisement, DNOS will not apply any modification for the attributes provided above if the path is an iBGP path. Even if it was explicitly required by the neighbor policy out.

To enable route-reflector policy-out attribute-change:


**Command syntax: route-reflection policy-out attribute-change [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Note**
- "Supported for default VRF and non-default VRF"
- "The behavior will apply for any neighbor there is a case of route reflection for and any address-family.
- "Configuration can co-exist with the ‘self-force’ option of policy set ipv4 next-hop / policy set ipv6 next-hop.
-- When the “route-reflector policy-out attribute-change” is enabled, the any next-hop modification option of policy set ipv4 next-hop / policy set ipv6 next-hop is imposed.
-- When the “route-reflector policy-out attribute-change” is disabled (default), only “self-force) the next-hop modification option of policy set ipv4 next-hop / policy set ipv6 next-hop is imposed when the reflecting routes act as the route-reflector.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Support modification of NEXT_HOP, AS_PATH, LOCAL_PREF and MED path attributes by | | enabled    | disabled |
|             | policy out when reflecting paths as Route-reflector                              | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# route-reflection policy-out attribute-change enabled


**Removing Configuration**

To disable this option:
::

    dnRouter(cfg-protocols-bgp)# no route-reflection policy-out attribute-change

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
