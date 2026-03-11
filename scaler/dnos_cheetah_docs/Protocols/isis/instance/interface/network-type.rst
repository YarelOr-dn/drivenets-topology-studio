protocols isis instance interface network-type
----------------------------------------------

**Minimum user role:** operator

You can configure the IS-IS interface to behave like a point-to-point connection. Configuring a point-to-point adjacency over a broadcast media can improve convergence times because it prevents the system from electing a designated router, prevents flooding from database synchronization, and simplifies SPF computations. This setting affects only IS-IS protocol procedures on the specific interface.

To configure the network-type for the interface:

**Command syntax: network-type [network-type]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface

**Parameter table**

+--------------+---------------------------------------------+----------------+----------------+
| Parameter    | Description                                 | Range          | Default        |
+==============+=============================================+================+================+
| network-type | Sets the adjacency type on the interface.   | point-to-point | point-to-point |
|              | Existing adjacencies will be reset.         |                |                |
+--------------+---------------------------------------------+----------------+----------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# network-type point-to-point


**Removing Configuration**

To revert to the default network type:
::

    dnRouter(cfg-isis-inst-if)# no network-type

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 6.0     | Command introduced                |
+---------+-----------------------------------+
| 9.0     | Removed "broadcast" network-type. |
+---------+-----------------------------------+
