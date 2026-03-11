interfaces ber-sf
-----------------

**Minimum user role:** operator

To enter Signal Failure alarm configuration level on an interface:

**Command syntax: ber-sf**

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
    dnRouter(cfg-if-ge100-1/1/1)# ber-sf
    dnRouter(cfg-if-ge100-1/1/1-sf)#


**Removing Configuration**

To revert Signal Failure settings to their default values:
::

    dnRouter(cfg-if-ge100-1/1/1)# no ber-sf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
