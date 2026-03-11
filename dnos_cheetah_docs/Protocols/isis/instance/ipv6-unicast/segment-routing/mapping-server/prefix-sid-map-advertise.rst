protocols isis instance address-family ipv6-unicast segment-routing mapping-server prefix-sid-map advertise
-----------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

This command enables the node as a mapping server. The router advertises binding SIDs according to the configured mapping (see "segment-routing mpls mapping-server prefix-sid-map" on page 2208).

To enable/disable the node as a mapping server:

**Command syntax: prefix-sid-map advertise [admin-state]** level [level]

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast segment-routing mapping-server

**Note**

- When the mapping server is enabled, the router always uses the local mapping, even if the mapping client functionality is disabled.

- The mapping server messages are not propagated between levels.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+---------------+-----------+
| Parameter   | Description                                                                      | Range         | Default   |
+=============+==================================================================================+===============+===========+
| admin-state | The administrative state of the mapping-server. When enabled, the router will    | | enabled     | disabled  |
|             | act as a segment-routing mapping server and will always use the local mapping,   | | disabled    |           |
|             | even if the mapping client functionality is disabled.                            |               |           |
+-------------+----------------------------------------------------------------------------------+---------------+-----------+
| level       | Defines for which IS-IS level the prefix-SID mapping will be advertised.         | | level-1     | level-1-2 |
|             |                                                                                  | | level-2     |           |
|             |                                                                                  | | level-1-2   |           |
+-------------+----------------------------------------------------------------------------------+---------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# segment-routing
    dnRouter(cfg-inst-afi-sr)# mapping-server
    dnRouter(cfg-afi-sr-mapping)# prefix-sid-map advertise enabled

    dnRouter(cfg-inst-afi-sr)# mapping-server
    dnRouter(cfg-afi-sr-mapping)# prefix-sid-map advertise enabled level level-1


**Removing Configuration**

To revert to the default value level advertisement:
::

    dnRouter(cfg-inst-afi-sr)# no prefix-sid-map advertise enabled level

To revert to the default advertise admin-state and level values:
::

    dnRouter(cfg-inst-afi-sr)# no prefix-sid-map advertise

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
