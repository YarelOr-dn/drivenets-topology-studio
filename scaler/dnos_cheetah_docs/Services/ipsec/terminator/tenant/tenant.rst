services ipsec terminator tenant
--------------------------------

**Minimum user role:** operator

DNOS supports IPSec tenant.

**Command syntax: tenant [tenant]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator

**Parameter table**

+-----------+----------------------------+-------+---------+
| Parameter | Description                | Range | Default |
+===========+============================+=======+=========+
| tenant    | Identifier for this tenant | \-    | \-      |
+-----------+----------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1
    dnRouter(cfg-srv-ipsec-term)# tenant 1


**Removing Configuration**

To remove the IPSec tenants configurations:
::

    dnRouter(cfg-srv-ipsec-term)# no tenant

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
