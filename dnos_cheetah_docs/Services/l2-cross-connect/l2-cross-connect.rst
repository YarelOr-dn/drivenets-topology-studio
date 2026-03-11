services l2-cross-connect
-------------------------

**Minimum user role:** operator


Circuit cross-connect allows to configure transparent connections between two circuits for the exchange of L2 data from one circuit to the other, and between two interfaces of the same type on the same router. This local switching connection works like a bridge domain with two bridge ports, where traffic enters from one endpoint of the local connection and leaves through the other.

To configure the l2 cross-connect:

#. Create an L2 cross-connect service.

#. Configure the two endpoints for the xConnect service. See "services l2-cross-connect interfaces".

#. Enable the xConnect service. See "services l2-cross-connect admin-state".

To create an L2 cross-connect service:

**Command syntax: l2-cross-connect [l2-cross-connect]**

**Command mode:** config

**Hierarchies**

- services

**Note**

- You can create up to 32 xConnect services per system.

**Parameter table**

+------------------+---------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                   | Range            | Default |
+==================+===============================================================+==================+=========+
| l2-cross-connect | Enters the context of L2 cross connect service configuration. | | string         | \-      |
|                  |                                                               | | length 1-255   |         |
+------------------+---------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# l2-cross-connect XC-To-Boston-CRS
    dnRouter(cfg-srv-l2xc)#


**Removing Configuration**

To delete a certain l2-cross-connect:
::

    dnRouter(cfg-srv)# no l2-cross-connect XC-To-Boston-CRS

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
