protocols isis instance forwarding-adjacency level
--------------------------------------------------

**Minimum user role:** operator

When using forwarding-adjacency, you must configure the level for which the forwarding-adjacency will be added: level-1 or level-2.

To configure the level for forwarding-adjacency:

**Command syntax: level [level]**

**Command mode:** config

**Hierarchies**

- protocols isis instance forwarding-adjacency

**Note**

- The tunnel must be configured to the same IS-IS instance.

- The same tunnel cannot be set as forwarding-adjacency in multiple IS-IS instances.

- The tunnel cannot be enabled with shortcut, either explicitly or inherit.

**Parameter table**

+-----------+-------------------------------------------------------------------+-------------+---------+
| Parameter | Description                                                       | Range       | Default |
+===========+===================================================================+=============+=========+
| level     | The IS-IS level for which the forwarding-adjacency will be added. | | level-1   | \-      |
|           |                                                                   | | level-2   |         |
+-----------+-------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# forwarding-adjacency TUNNEL_1
    dnRouter(cfg-isis-inst-fa)# level level-2


**Removing Configuration**

To remove the level configuration:
::

    dnRouter(cfg-isis-inst-fa)# no level

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2    | Command introduced |
+---------+--------------------+
