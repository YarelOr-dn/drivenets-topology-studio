services ipsec terminator tenant organization vrf
-------------------------------------------------

**Minimum user role:** operator

DNOS supports IPSec vrf.

**Command syntax: vrf [vrf]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator tenant organization

**Parameter table**

+-----------+----------------------------------+----------------+---------+
| Parameter | Description                      | Range          | Default |
+===========+==================================+================+=========+
| vrf       | vrf-name within the organization | string         | \-      |
|           |                                  | length 1-255   |         |
+-----------+----------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1
    dnRouter(cfg-srv-ipsec-term)# tenant 1
    dnRouter(cfg-srv-ipsec-term-tenant)# org 1
    dnRouter(cfg-srv-ipsec-term-tenant-org)# vrf vrf1


**Removing Configuration**

To remove the IPSec vrfs configurations:
::

    dnRouter(cfg-srv-ipsec-term-org-vrf)# no vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
