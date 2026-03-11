protocols segment-routing pcep source interface
-----------------------------------------------

**Minimum user role:** operator

To configure the PCEP source (either an IPv4 address or an interface):

**Command syntax: source interface [interface]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep

**Parameter table**

+-----------+----------------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                          | Range            | Default |
+===========+======================================================================+==================+=========+
| interface | interface from which the ipv4 address will be used as source address | | string         | \-      |
|           |                                                                      | | length 1-255   |         |
+-----------+----------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)# source interface lo0


**Removing Configuration**

To revert to the default source address (the MPLS TE router-id):
::

    dnRouter(cfg-protocols-sr-pcep)# no source

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
