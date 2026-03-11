network-services nat
--------------------

**Minimum user role:** operator

To enter the NAT configuration hierarchy under network-services:

**Command syntax: nat**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)#


**Removing Configuration**

The remove all NAT instances
::

    dnRouter(cfg-netsrv)# no nat

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
