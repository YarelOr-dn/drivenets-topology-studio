protocols lacp interface period
-------------------------------

**Minimum user role:** operator

To configure the frequency with which PDUs are sent to the partner system:

**Command syntax: period [period]**

**Command mode:** config

**Hierarchies**

- protocols lacp interface

**Parameter table**

+-----------+--------------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                    | Range     | Default |
+===========+================================================================================+===========+=========+
| period    | Set the period between LACP messages -- uses the lacp-period-type enumeration. | | short   | long    |
|           |                                                                                | | long    |         |
+-----------+--------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lacp

    dnRouter(cfg-protocols-lacp)# interface bundle-2
    dnRouter(cfg-protocols-lacp-if)# period short

    dnRouter(cfg-protocols-lacp)# interface bundle-1
    dnRouter(cfg-protocols-lacp-if)# period long


**Removing Configuration**

To revert to the default configuration:
::

    dnRouter(cfg-protocols-lacp-if)# no period

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 6.0     | Command introduced    |
+---------+-----------------------+
| 10.0    | Applied new hierarchy |
+---------+-----------------------+
