services ipsec terminator ike-lo-interface
------------------------------------------

**Minimum user role:** operator

Set the name of the ike loopback interface above the ike sub-interface.

**Command syntax: ike-lo-interface [ike-lo-interface]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator

**Parameter table**

+------------------+------------------------------------------+----------------+---------+
| Parameter        | Description                              | Range          | Default |
+==================+==========================================+================+=========+
| ike-lo-interface | ike lo interface above ike sub-interface | string         | \-      |
|                  |                                          | length 1-255   |         |
+------------------+------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1
    dnRouter(cfg-srv-ipsec-term)# ike-lo-interface lo3


**Removing Configuration**

To remove the configuration of the ike loopback interface:
::

    dnRouter(cfg-srv-ipsec-term)# no ike-lo-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
