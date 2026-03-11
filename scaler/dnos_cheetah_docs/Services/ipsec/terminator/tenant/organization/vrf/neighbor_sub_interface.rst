services ipsec terminator tenant organization vrf neighbor-sub-interface
------------------------------------------------------------------------

**Minimum user role:** operator

Set the name of the neighbour sub interface which is conntected to ipsec-terminator.

**Command syntax: neighbor-sub-interface [neighbor-sub-interface]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator tenant organization vrf

**Parameter table**

+------------------------+------------------------------------------------------------------+----------------+---------+
| Parameter              | Description                                                      | Range          | Default |
+========================+==================================================================+================+=========+
| neighbor-sub-interface | sub-interface name allocated to the vrf in this ipsec-terminator | string         | \-      |
|                        |                                                                  | length 1-255   |         |
+------------------------+------------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1
    dnRouter(cfg-srv-ipsec-term)# tenant 1
    dnRouter(cfg-srv-ipsec-term-tenant)# org 1
    dnRouter(cfg-srv-ipsec-term-tenant-org)# vrf vrf1 neighbor-sub-interface bundle-2.100


**Removing Configuration**

To remove the configuration of the neighbor sub interface:
::

    dnRouter(cfg-srv-ipsec-term)# no neighbor-sub-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
