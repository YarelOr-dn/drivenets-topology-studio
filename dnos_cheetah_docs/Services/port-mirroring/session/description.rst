services port-mirroring session description
-------------------------------------------

**Minimum user role:** operator

To define a description for a specific port-mirroring session:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- services port-mirroring session

**Parameter table**

+-------------+------------------------------------+------------------+---------+
| Parameter   | Description                        | Range            | Default |
+=============+====================================+==================+=========+
| description | Port mirroring session description | | string         | \-      |
|             |                                    | | length 1-255   |         |
+-------------+------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# port-mirroring
    dnRouter(cfg-srv-port-mirroring)# session IDS-Debug
    dnRouter(cfg-srv-port-mirroring-session)# description Test_session1


**Removing Configuration**

To remove the description of the session:
::

    dnRouter(cfg-srv-port-mirroring-session)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
