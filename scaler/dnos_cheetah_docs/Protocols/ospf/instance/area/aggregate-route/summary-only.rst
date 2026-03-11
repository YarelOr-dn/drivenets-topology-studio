protocols ospf instance area aggregate-route summary-only
---------------------------------------------------------

**Minimum user role:** operator

To advertise only the aggregate route and not the contributing individual summary routes:

**Command syntax: summary-only**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area aggregate-route

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# aggregate-route 3.3.0.0/16
    dnRouter(cfg-ospf-area-aggregate)# summary-only


**Removing Configuration**

To revert to default behavior:
::

    dnRouter(cfg-ospf-area-aggregate)# no summary-only

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
