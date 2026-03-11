qos traffic-class-map
---------------------

**Minimum user role:** operator

A QoS traffic-class-map is a set of packet attributes that match criteria identified by a unique name.

To create a QoS traffic-class-map:

**Command syntax: traffic-class-map [traffic-class-map]**

**Command mode:** config

**Hierarchies**

- qos

**Note**

- You cannot remove a traffic-class-map if it is used in a policy.

**Parameter table**

+-------------------+--------------------------------------------------+------------------+---------+
| Parameter         | Description                                      | Range            | Default |
+===================+==================================================+==================+=========+
| traffic-class-map | References the configured name of the classifier | | string         | \-      |
|                   |                                                  | | length 1-255   |         |
+-------------------+--------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1


**Removing Configuration**

To remove the traffic-class-map:
::

    dnRouter(cfg-qos)# no traffic-class-map MyTrafficClass1

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 11.2    | Command re-introduced |
+---------+-----------------------+
