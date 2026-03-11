services ipsec tunnel vrf neighbor-sub-interface
------------------------------------------------

**Minimum user role:** operator

Set the neighbor-sub-interface for the tunnel to connect to.

**Command syntax: neighbor-sub-interface [neighbor-sub-interface]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf

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
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# neighbor-sub-interface ge100-0/0/0.501


**Removing Configuration**

To remove the configuration of the neighbor-sub-interface:
::

    dnRouter(cfg-srv-ipsec-tun)# no neighbor-sub-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
