services ipsec
--------------

**Minimum user role:** operator

DNOS supports IPSec service.

**Command syntax: ipsec**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)#


**Removing Configuration**

To remove the IPSec configurations:
::

    dnRouter(cfg-srv)# no ipsec

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
