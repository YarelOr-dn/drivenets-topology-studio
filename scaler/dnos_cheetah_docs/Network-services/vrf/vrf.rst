network-services vrf
--------------------

**Minimum user role:** operator

To enter the VRF configuration hierarchy under network-services:

**Command syntax: vrf**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf
    dnRouter(cfg-netsrv-vrf)#


**Removing Configuration**

The remove non-default VRFs and restore default VRFs:
::

    dnRouter(cfg-netsrv)# no vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
