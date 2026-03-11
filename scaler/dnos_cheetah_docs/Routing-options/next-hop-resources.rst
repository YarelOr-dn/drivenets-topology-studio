routing-options next-hop-resources threshold
--------------------------------------------

**Minimum user role:** operator

To configure the warning threshold for the next-hop resources in use:

**Command syntax: next-hop-resources threshold [threshold]**

**Command mode:** config

**Hierarchies**

- routing-options

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                      | Range     | Default |
+===========+==================================================================================+===========+=========+
| threshold | percent of max scale for which a syslog event will be sent when crossing         | 0, 50-100 | 75      |
|           | threshold                                                                        |           |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# next-hop-resources threshold 80
    dnRouter(cfg-routing-option)#


**Removing Configuration**

To revert the threshold to its default: 75%
::

    dnRouter(cfg-routing-option)# no next-hop-resources threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
