protocols isis instance shortcut-usage
--------------------------------------

**Minimum user role:** operator

Set if IS-IS will run shortcut calculation to find shortcut paths using lsp nexthop and install them in mpls-nh table. If enabled, no forwarding-adjacency link can be configured for the IS-IS instance.
Behavior applies for all IS-IS levels.

**Command syntax: shortcut-usage [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | Set if ISIS will run shortcut calculation to find shortcut paths using lsp       | | enabled    | enabled |
|             | nexthop and install them in mpls-nh table.                                       | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# shortcut-usage enabled

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# shortcut-usage disabled


**Removing Configuration**

To revert the shortcut-usage to its default value:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no shortcut-usage

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2    | Command introduced |
+---------+--------------------+
