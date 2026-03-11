services ipsec terminator
-------------------------

**Minimum user role:** operator

DNOS supports IPSec terminator.

**Command syntax: terminator [ipsec-terminator]**

**Command mode:** config

**Hierarchies**

- services ipsec

**Parameter table**

+------------------+---------------------------------------------------------+-------+---------+
| Parameter        | Description                                             | Range | Default |
+==================+=========================================================+=======+=========+
| ipsec-terminator | unique identifier in service-node per ipsec-terminator. | 0-255 | \-      |
+------------------+---------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator
    dnRouter(cfg-srv-ipsec-term)#


**Removing Configuration**

To remove the IPSec terminators configurations:
::

    dnRouter(cfg-srv-ipsec)# no terminator

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
