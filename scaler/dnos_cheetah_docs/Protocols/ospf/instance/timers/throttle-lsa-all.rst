protocols ospf instance timers throttle lsa all hold-interval start-interval max-interval
-----------------------------------------------------------------------------------------

**Minimum user role:** operator

OSPF LSA throttling provides a dynamic mechanism to slow down link-state advertisement (LSA) updates in OSPF during times of network instability. It also allows faster OSPF convergence by providing LSA rate limiting in milliseconds.
The first LSA that is generated uses the start-interval timer, so it is generated after start-interval milliseconds. If the same LSA has to be re-generated, it will use the lsa-hold value instead. When the LSA has to be generated the third time, the lsa-hold value will double.
Each time the LSA is re-generated, the lsa-hold value will double until it reaches the lsa-max value.
An LSA is considered the same if the following three values are the same: (1) LSA ID number (2) LSA type (3) advertising router ID.

**Command syntax: throttle lsa all hold-interval [hold-interval] start-interval [start-interval] max-interval [max-interval]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance timers

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
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# timers throttle lsa all hold-interval 100 start-interval 5 max-interval 5000


**Removing Configuration**

The no timers throttle lsa all command reverts LSA throttling timers to their default values.
::

    dnRouter(cfg-protocols-ospf)# no timers throttle lsa all

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
