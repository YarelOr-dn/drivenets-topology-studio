services ipsec terminator ike-sub-interface
-------------------------------------------

**Minimum user role:** operator

Set the name of the ike sub interface which is conntected to ipsec-terminator.

**Command syntax: ike-sub-interface [ike-sub-interface]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator

**Parameter table**

+-------------------+-------------------------------------------------+----------------+---------+
| Parameter         | Description                                     | Range          | Default |
+===================+=================================================+================+=========+
| ike-sub-interface | ike sub-interface connected to ipsec-terminator | string         | \-      |
|                   |                                                 | length 1-255   |         |
+-------------------+-------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1
    dnRouter(cfg-srv-ipsec-term)# ike-sub-interface ge100-0/0/2.100


**Removing Configuration**

To remove the configuration of the ike sub interface:
::

    dnRouter(cfg-srv-ipsec-term)# no ike-sub-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
