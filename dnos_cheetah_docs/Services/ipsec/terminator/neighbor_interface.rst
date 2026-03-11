services ipsec terminator neighbor-interface
--------------------------------------------

**Minimum user role:** operator

Set the name of the interface the ipsec-terminator will connect to.

**Command syntax: neighbor-interface [neighbor-interface]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator

**Parameter table**

+--------------------+-----------------------------------------------------+----------------+---------+
| Parameter          | Description                                         | Range          | Default |
+====================+=====================================================+================+=========+
| neighbor-interface | interface name the ipsec-terminator is connected to | string         | \-      |
|                    |                                                     | length 1-255   |         |
+--------------------+-----------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1
    dnRouter(cfg-srv-ipsec-term)# neighbor-interface ge100-0/0/2


**Removing Configuration**

To remove the configureation of the neighbour interface:
::

    dnRouter(cfg-srv-ipsec-term)# no neighbor-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
