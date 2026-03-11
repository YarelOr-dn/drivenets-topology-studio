interfaces dampening reuse-threshold
------------------------------------

**Minimum user role:** operator

When the dampening threshold falls below the reuse-threshold, the interface becomes available again. To configure the interface dampening reuse threshold:

**Command syntax: reuse-threshold [reuse-threshold]**

**Command mode:** config

**Hierarchies**

- interfaces dampening

**Note**

- The command is applicable to physical interfaces.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                                      | Range   | Default |
+=================+==================================================================================+=========+=========+
| reuse-threshold | The minimum threshold below which the interface becomes available again. The     | 1-19999 | 750     |
|                 | value must be lower than the suppress-threshold.                                 |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1
    dnRouter(cfg-if-ge100-1/0/1)# dampening
    dnRouter(cfg-if-ge100-1/0/1-dampening)# reuse-threshold 1100
    dnRouter(cfg-if-ge100-1/0/1-dampening)#

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/13
    dnRouter(cfg-if-ge100-1/0/13)# dampening
    dnRouter(cfg-if-ge100-1/0/13-dampening)# half-life 100 reuse-threshold 1100 suppress-threshold 2500 max-suppress 2000
    dnRouter(cfg-if-ge100-1/0/13-dampening)#


**Removing Configuration**

To revert to the default value
::

    dnRouter(cfg-if-ge100-1/0/13-dampening)# no reuse-threshold 1100

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
