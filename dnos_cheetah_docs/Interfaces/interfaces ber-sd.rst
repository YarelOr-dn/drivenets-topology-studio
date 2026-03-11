interfaces ber-sd
-----------------

**Minimum user role:** operator

To enter Signal Degrade alarm configuration level on an interface:

**Command syntax: ber-sd**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**
- The command is applicable only to 400G and 100G physical interfaces with FEC.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# ber-sd
    dnRouter(cfg-if-ge100-1/1/1-sd)#


**Removing Configuration**

To revert Signal Degrade settings to their default values:
::

    dnRouter(cfg-if-ge100-1/1/1)# no ber-sd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
