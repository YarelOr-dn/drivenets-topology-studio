protocols isis instance address-family ipv4-unicast segment-routing admin-state
-------------------------------------------------------------------------------

**Minimum user role:** operator

This command enables/disables segment-routing in IS-IS for source routing using MPLS SID. When enabled, segment-routing information is exchanged with all IS-IS neighbors. 

To enable/disable segment-routing:


**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast segment-routing

**Note**

- Segment-routing can be enabled for a single IS-IS instance only.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | The administrative state of segment routing. When   enabled, segment-routing     | | enabled    | disabled |
|             | information is exchanged with all IS-IS neighbors.                               | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
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
| 14.0    | Command introduced |
+---------+--------------------+
