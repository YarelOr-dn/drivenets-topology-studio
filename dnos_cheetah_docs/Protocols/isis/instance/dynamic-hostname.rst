protocols isis instance dynamic-hostname
----------------------------------------

**Minimum user role:** operator

IS-IS uses a 6 byte system ID to represent a node in the network (in hexadecimal values). Hexadecimal representations are not as clear as device names, and so you may want to map these system IDs to their device names for monitoring, operation, and troubleshooting tasks.

Enabling the dynamic hostname feature allows the IS-IS routers to include the name-to-systemID mapping data in their link-state PDUs (LSPs).

To enable the support for dynamic hostname:


**Command syntax: dynamic-hostname [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Parameter table**

+-------------+-----------------------------------------------------------+--------------+---------+
| Parameter   | Description                                               | Range        | Default |
+=============+===========================================================+==============+=========+
| admin-state | The administrative state of the dynamic hostname feature. | | enabled    | enabled |
|             |                                                           | | disabled   |         |
+-------------+-----------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# dynamic-hostname enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-isis-inst-afi)# no dynamic-hostname

**Command History**

+---------+-----------------------------------------------------------------------+
| Release | Modification                                                          |
+=========+=======================================================================+
| 6.0     | Command introduced                                                    |
+---------+-----------------------------------------------------------------------+
| 9.0     | Changed argument syntax from "hostname dynamic" to "dynamic-hostname" |
+---------+-----------------------------------------------------------------------+
