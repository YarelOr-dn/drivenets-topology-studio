network-services multihoming interface designated-forwarder algorithm
---------------------------------------------------------------------

**Minimum user role:** operator

Defines the algorithm that the user would like to use for choosing the Default Forwarder.
The actual algorithm used will depend on agreement between all the PEs attached to the same ES.

**Command syntax: algorithm [algorithm]**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface designated-forwarder

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
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# designated-forwarder
    dnRouter(cfg-mh-int-df)# algorithm mod
    dnRouter(cfg-mh-int-df)#


**Removing Configuration**

To restore the algorithm to its default value.
::

    dnRouter(cfg-mh-int-df)# no algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
