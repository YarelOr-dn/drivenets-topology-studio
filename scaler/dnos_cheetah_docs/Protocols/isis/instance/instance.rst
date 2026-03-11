protocols isis instance
-----------------------

**Minimum user role:** operator

IS-IS instances allow you to set different IS-IS configuration per instance, using the same system-id and loopback interfaces. However, each instance must be configured with a different administrative-distance. You can configure up to 5 IS-IS instances, each with a unique name.

To start an IS-IS instance, set its ISO routing area tag and enter its configuration hierarchy

**Command syntax: instance [isis-instance-name]**

**Command mode:** config

**Hierarchies**

- protocols isis

**Note**

- IS-IS works with metric style wide by default.

- The IS-IS router-id is identical in all isis instances.

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter          | Description                                                                      | Range            | Default |
+====================+==================================================================================+==================+=========+
| isis-instance-name | The IS-IS instance name identifies the specific IS-IS protocol instance. The     | | string         | \-      |
|                    | name cannot be changed. If you need to change it, you must delete the IS-IS      | | length 1-255   |         |
|                    | protocol instance using the no instance [isis-instance-name] command and         |                  |         |
|                    | reconfigure with a different name.                                               |                  |         |
+--------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# instance area_2
    dnRouter(cfg-protocols-isis-inst)#


**Removing Configuration**

To remove all IS-IS protocol instances:
::

    dnRouter(cfg-protocols-isis)# no instance

To remove a specific IS-IS protocol instance:
::

    dnRouter(cfg-protocols-isis)# no instance area_2

**Command History**

+---------+--------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                             |
+=========+==========================================================================================================================+
| 6.0     | Command introduced                                                                                                       |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 9.0     | Changed "area-tag" to "isis-instance-name"                                                                               |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 10.0    | Added support for multiple instances                                                                                     |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 11.0    | Moved command underneath the isis hierarchy (instead of directly under the protocols hierarchy) and changed the syntax   |
|         | accordingly from "isis [value]" to "instance [value]".                                                                   |
+---------+--------------------------------------------------------------------------------------------------------------------------+
