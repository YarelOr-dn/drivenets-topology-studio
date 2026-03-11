services ipsec terminator internet-sub-interface
------------------------------------------------

**Minimum user role:** operator

Set the name of the internet sub interface which is conntected to ipsec-terminator.

**Command syntax: internet-sub-interface [internet-sub-interface]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator

**Parameter table**

+------------------------+------------------------------------------------------+----------------+---------+
| Parameter              | Description                                          | Range          | Default |
+========================+======================================================+================+=========+
| internet-sub-interface | internet sub-interface connected to ipsec-terminator | string         | \-      |
|                        |                                                      | length 1-255   |         |
+------------------------+------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1
    dnRouter(cfg-srv-ipsec-term)# internet-sub-interface ge100-0/0/2.100


**Removing Configuration**

To remove the configuration of the internet sub interface:
::

    dnRouter(cfg-srv-ipsec-term)# no internet-sub-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
