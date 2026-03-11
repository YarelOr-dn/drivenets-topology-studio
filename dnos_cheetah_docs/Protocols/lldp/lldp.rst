protocols lldp
--------------

**Minimum user role:** operator

To enter LLDP configuration mode:"

**Command syntax: lldp**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The lldp protocol is applicable for default vrf only.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)#


**Removing Configuration**

To remove the LLDP protocol
::

    dnRouter(cfg-protocols)# no lldp

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 7.0     | Command introduced            |
+---------+-------------------------------+
| 9.0     | Not supported in this version |
+---------+-------------------------------+
| 10.0    | Command reintroduced          |
+---------+-------------------------------+
