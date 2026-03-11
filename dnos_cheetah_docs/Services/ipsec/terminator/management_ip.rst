services ipsec terminator management-ip
---------------------------------------

**Minimum user role:** operator

Sets the management ip used for accessing the terminator.

**Command syntax: management-ip [management-ip]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator

**Parameter table**

+---------------+----------------------------------+------------+---------+
| Parameter     | Description                      | Range      | Default |
+===============+==================================+============+=========+
| management-ip | Terminator management ip address | A.B.C.D    | \-      |
|               |                                  | X:X::X:X   |         |
+---------------+----------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1 management-ip 1.2.3.4


**Removing Configuration**

To revert the admis-state to the default value:
::

    dnRouter(cfg-srv-ipsec)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
