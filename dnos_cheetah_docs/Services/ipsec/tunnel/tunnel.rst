services ipsec tunnel vrf
-------------------------

**Minimum user role:** operator

configuration of device which will connect to IPSec gateway.

**Command syntax: tunnel [device-id] vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- services ipsec

**Parameter table**

+-----------+----------------------------------+----------------+---------+
| Parameter | Description                      | Range          | Default |
+===========+==================================+================+=========+
| device-id | unique identifier per device.    | \-             | \-      |
+-----------+----------------------------------+----------------+---------+
| vrf-name  | vrf name within the organization | string         | \-      |
|           |                                  | length 1-255   |         |
+-----------+----------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf my_vrf
    dnRouter(cfg-srv-ipsec-tun)#


**Removing Configuration**

To remove the tunnel configurations:
::

    dnRouter(cfg-srv-ipsec)# no tunnel 1 vrf my_vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
