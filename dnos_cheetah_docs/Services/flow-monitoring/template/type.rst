services flow-monitoring template type
--------------------------------------

**Minimum user role:** operator

To define the type of traffic to monitored using the specified template:

**Command syntax: type [type]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring template

**Note**
-  Traffic flows will not be tracked for ipv4-over-mpls and ipv6-over-mpls templates if speculative parser is off.

**Parameter table**

+-----------+---------------+--------------------+---------+
| Parameter | Description   | Range              | Default |
+===========+===============+====================+=========+
| type      | template type | | ipv4             | \-      |
|           |               | | ipv6             |         |
|           |               | | ipv4-over-mpls   |         |
|           |               | | ipv6-over-mpls   |         |
+-----------+---------------+--------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# template myTemplate
    dnRouter(cfg-srv-flow-monitoring-myTemplate)# type ipv4-over-mpls


**Removing Configuration**

To remove the type:
::

    dnRouter(cfg-srv-flow-monitoring-myTemplate)# no type

**Command History**

+---------+------------------------------------------+
| Release | Modification                             |
+=========+==========================================+
| 11.4    | Command introduced                       |
+---------+------------------------------------------+
| 13.2    | Remove 'no command' as type is mandatory |
+---------+------------------------------------------+
