interfaces dampening suppress-threshold
---------------------------------------

**Minimum user role:** operator

Suppress-threshold determines when the advertisement of the interface state starts. To configure the dampening suppress threshold for an interface:

**Command syntax: suppress-threshold [suppress-threshold]**

**Command mode:** config

**Hierarchies**

- interfaces dampening

**Note**

- The command is applicable to physical interfaces.

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter          | Description                                                                      | Range   | Default |
+====================+==================================================================================+=========+=========+
| suppress-threshold | The threshold to start suppressing the advertisement of the interface state. The | 2-20000 | 2000    |
|                    | suppress-threshold value cannot be lower than the reuse-threshold value.         |         |         |
+--------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1
    dnRouter(cfg-if-ge100-1/0/1)# dampening
    dnRouter(cfg-if-ge100-1/0/1-dampening)# suppress-threshold 2500
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

    dnRouter(cfg-if-ge100-1/0/13-dampening)# no suppress-threshold

**Command History**

+---------+--------------------------------------+
| Release | Modification                         |
+=========+======================================+
| 11.4    | Command introduced                   |
+---------+--------------------------------------+
| 11.5    | Updated the suppress-threshold range |
+---------+--------------------------------------+
