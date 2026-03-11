network-services multihoming redundancy-mode
--------------------------------------------

**Minimum user role:** operator

Sets the default redundancy-mode - single-active or all-active.

**Command syntax: redundancy-mode [redundancy-mode]**

**Command mode:** config

**Hierarchies**

- network-services multihoming

**Parameter table**

+-----------------+---------------------------------------------+-------------------+------------+
| Parameter       | Description                                 | Range             | Default    |
+=================+=============================================+===================+============+
| redundancy-mode | interface type, single-active or all-active | | single-active   | all-active |
|                 |                                             | | all-active      |            |
|                 |                                             | | port-active     |            |
+-----------------+---------------------------------------------+-------------------+------------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# redundancy-mode single-active
    dnRouter(cfg-netsrv-mh)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh)# no redundancy-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
