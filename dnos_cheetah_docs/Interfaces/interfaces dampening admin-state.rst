interfaces dampening admin-state
--------------------------------

**Minimum user role:** operator

To enable/disable interface dampening on the interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces dampening

**Note**

- The command is applicable to physical interfaces.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | The administrative state of the dampening feature for the specific interface.    | | enabled    | disabled |
|             | When enabled, advertisement of state changes will act according to the           | | disabled   |          |
|             | configured dampening parameters.                                                 |              |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1
    dnRouter(cfg-if-ge100-1/0/1)# dampening
    dnRouter(cfg-if-ge100-1/0/1-dampening)# admin-state enabled
    dnRouter(cfg-if-ge100-1/0/1-dampening)#

    dnRouter# configure
    dnRouter(cfg)# interfaces ge100-1/0/12
    dnRouter(cfg-if-ge100-1/0/12)# dampening
    dnRouter(cfg-if-ge100-1/0/12-dampening)# admin-state disabled
    dnRouter(cfg-if-ge100-1/0/12-dampening)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-ge100-1/0/12-dampening)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
