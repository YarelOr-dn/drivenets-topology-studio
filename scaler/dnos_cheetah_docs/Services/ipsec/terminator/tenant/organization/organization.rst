services ipsec terminator tenant organization
---------------------------------------------

**Minimum user role:** operator

DNOS supports IPSec organization.

**Command syntax: organization [organization]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator tenant

**Parameter table**

+--------------+----------------------------------+-------+---------+
| Parameter    | Description                      | Range | Default |
+==============+==================================+=======+=========+
| organization | Identifier for this organization | \-    | \-      |
+--------------+----------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1
    dnRouter(cfg-srv-ipsec-term)# tenant 1
    dnRouter(cfg-srv-ipsec-term-tenant)# organization 1


**Removing Configuration**

To remove the IPSec organizations configurations:
::

    dnRouter(cfg-srv-ipsec-term-org)# no organization

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
