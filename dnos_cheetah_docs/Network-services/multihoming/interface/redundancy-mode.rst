network-services multihoming interface redundancy-mode
------------------------------------------------------

**Minimum user role:** operator

Sets the redundancy-mode for the AC interface -  all-active, single-active or port-active. 

**Command syntax: redundancy-mode [redundancy-mode]**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface

**Parameter table**

+-----------------+----------------------------------------------------------+-------------------+---------+
| Parameter       | Description                                              | Range             | Default |
+=================+==========================================================+===================+=========+
| redundancy-mode | interface type, single-active, port-active or all-active | | single-active   | \-      |
|                 |                                                          | | all-active      |         |
|                 |                                                          | | port-active     |         |
+-----------------+----------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# redundancy-mode single-active


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh-int)# no redundancy-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
