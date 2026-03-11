interfaces dampening max-suppress
---------------------------------

**Minimum user role:** operator

This command limits the amount of time that the advertisement of the interface's state is suppressed. To configure the maximum number of seconds that an interface can be suppressed by the device:

**Command syntax: max-suppress [max-suppress]**

**Command mode:** config

**Hierarchies**

- interfaces dampening

**Note**

- The command is applicable to physical interfaces.

**Parameter table**

+--------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter    | Description                                                                      | Range   | Default |
+==============+==================================================================================+=========+=========+
| max-suppress | The maximum number of seconds that an interface can be suppressed by the device. | 2-43200 | 300     |
+--------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1
    dnRouter(cfg-if-ge100-1/0/1)# dampening
    dnRouter(cfg-if-ge100-1/0/1-dampening)# max-suppress 250
    dnRouter(cfg-if-ge100-1/0/1-dampening)#

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/13
    dnRouter(cfg-if-ge100-1/0/13)# dampening
    dnRouter(cfg-if-ge100-1/0/13-dampening)# half-life 100 reuse-threshold 1100 suppress-threshold 2500 max-suppress 2000
    dnRouter(cfg-if-ge100-1/0/13-dampening)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-ge100-1/0/13-dampening)# no max-suppress

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
