services ipsec terminator public-ip
-----------------------------------

**Minimum user role:** operator

Sets the public ip used for accessing the terminator.

**Command syntax: public-ip [public-ip]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator

**Parameter table**

+-----------+--------------------------------------------+------------+---------+
| Parameter | Description                                | Range      | Default |
+===========+============================================+============+=========+
| public-ip | Public IP address of the ipsec-terminator. | A.B.C.D    | \-      |
|           |                                            | X:X::X:X   |         |
+-----------+--------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1 public-ip 1.2.3.4


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
