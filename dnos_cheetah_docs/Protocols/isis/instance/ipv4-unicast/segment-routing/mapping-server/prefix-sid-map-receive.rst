protocols isis instance address-family ipv4-unicast segment-routing mapping-server prefix-sid-map receive
---------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

This command enables the node as a mapping client. A mapping client can server multiple mapping servers.

To enable/disable the node as a mapping client:

**Command syntax: prefix-sid-map receive [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast segment-routing mapping-server

**Note**

- When mapping server is enabled, the router will always use the local mapping, even if the mapping client functionality is disabled.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | The administrative state of the mapping-client. When enabled, the router will    | | enabled    | enabled |
|             | act as a segment-routing mapping client.                                         | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# segment-routing
    dnRouter(cfg-inst-afi-sr)# mapping-server
    dnRouter(cfg-afi-sr-mapping)# prefix-sid-map receive enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-inst-afi-sr)# no prefix-sid-map receive

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+
