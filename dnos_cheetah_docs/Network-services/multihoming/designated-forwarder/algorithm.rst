network-services multihoming designated-forwarder algorithm
-----------------------------------------------------------

**Minimum user role:** operator

Defines the default value for the algorithm that the user would like to use for choosing the Designated Forwarder.
This value can be modified per interface by setting the per interface knob.

**Command syntax: algorithm [algorithm]**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Parameter table**

+-----------+---------------------------------------+----------------------+---------+
| Parameter | Description                           | Range                | Default |
+===========+=======================================+======================+=========+
| algorithm | algorithm to calculate the DF and BDF | mod                  | mod     |
|           |                                       | highest-preference   |         |
+-----------+---------------------------------------+----------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)# algorithm mod
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To restore the default value of the algorithm to mod.
::

    dnRouter(cfg-netsrv-mh-df)# no algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
