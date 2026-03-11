protocols isis instance address-family ipv6-unicast segment-routing admin-state
-------------------------------------------------------------------------------

**Minimum user role:** operator

Enable segment-routing in IS-IS, for source routing using MPLS SID.
Once enabled, segment-routing information will be exchanged will all isis neighbors.


**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast segment-routing

**Parameter table**

+-------------+---------------------------------------------+--------------+----------+
| Parameter   | Description                                 | Range        | Default  |
+=============+=============================================+==============+==========+
| admin-state | Enable IGP segment routing for ipv6-unicast | | enabled    | disabled |
|             |                                             | | disabled   |          |
+-------------+---------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# segment-routing
    dnRouter(cfg-inst-afi-sr)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-inst-afi-sr)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
