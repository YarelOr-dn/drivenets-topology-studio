protocols ospfv3 timers throttle lsa all hold-interval start-interval max-interval
----------------------------------------------------------------------------------

**Minimum user role:** operator

The OSPFV3 process describes its transit links in its router-LSA as having infinite distance so that other routers will avoid calculating transit paths through the router while still being able to reach networks through the router. 
To configure the OSPFV3 protocol to advertise a router-LSA with a maximum metric value (65535) on system startup for all links for the configured time interval:

**Command syntax: throttle lsa all hold-interval [hold-interval] start-interval [start-interval] max-interval [max-interval]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 timers

**Parameter table**

+----------------+------------------------------+----------+---------+
| Parameter      | Description                  | Range    | Default |
+================+==============================+==========+=========+
| hold-interval  | timer for second LSA message | 0-500000 | 200     |
+----------------+------------------------------+----------+---------+
| start-interval | Initial LSA schedule delay.  | 0-500000 | 50      |
+----------------+------------------------------+----------+---------+
| max-interval   | timer for second LSA message | 0-500000 | 5000    |
+----------------+------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospfv3
    dnRouter(cfg-protocols-ospfv3)# timers throttle lsa all hold-interval 100 start-interval 5 max-interval 5000


**Removing Configuration**

The no timers throttle lsa all command reverts LSA throttling timers to their default values.
::

    dnRouter(cfg-protocols-ospfv3)# no timers throttle lsa all

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
