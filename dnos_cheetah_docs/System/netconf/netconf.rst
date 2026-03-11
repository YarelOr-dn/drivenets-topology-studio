system netconf
--------------

**Minimum user role:** operator

To configure a Netconf server:

**Command syntax: netconf**

**Command mode:** config

**Hierarchies**

- system

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# netconf
    dnRouter(cfg-system-netconf)#


**Removing Configuration**

To revert all netconf configuration to default:
::

    dnRouter(cfg-system)# no netconf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
