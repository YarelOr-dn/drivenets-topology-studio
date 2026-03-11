system network-resources resource public-interface
--------------------------------------------------

**Minimum user role:** operator

Set the name of the public interface for the ipsec server.

**Command syntax: public-interface [public-interface]**

**Command mode:** config

**Hierarchies**

- system network-resources resource

**Parameter table**

+------------------+----------------------------------------------------+------------------+---------+
| Parameter        | Description                                        | Range            | Default |
+==================+====================================================+==================+=========+
| public-interface | loopback interface configured for the ipsec server | | string         | \-      |
|                  |                                                    | | length 1-255   |         |
+------------------+----------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# network-resources
    dnRouter(cfg-system-netres)# resource ipsec-server-1
    dnRouter(cfg-system-netres-res)# public-interface lo0


**Removing Configuration**

To remove the configuration of the public interface:
::

    dnRouter(cfg-system-netres-res)# no public-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
