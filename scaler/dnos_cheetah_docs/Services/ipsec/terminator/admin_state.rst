services ipsec terminator admin-state
-------------------------------------

**Minimum user role:** operator

Control whether a given IPSec terminator is enabled or not.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator

**Parameter table**

+-------------+-----------------------------------------+------------+---------+
| Parameter   | Description                             | Range      | Default |
+=============+=========================================+============+=========+
| admin-state | set whether ipsec terminator is enabled | enabled    | enabled |
|             |                                         | disabled   |         |
+-------------+-----------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1 admin-state enabled


**Removing Configuration**

To revert the admin-state to the default value:
::

    dnRouter(cfg-srv-ipsec)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
