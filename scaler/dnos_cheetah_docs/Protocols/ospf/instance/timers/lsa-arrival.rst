protocols ospf instance timers lsa-arrival
------------------------------------------

**Minimum user role:** operator

Sets the minimum interval to accept the same LSA, in milliseconds.

**Command syntax: lsa-arrival [timer-lsa-arrival]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance timers

**Parameter table**

+-------------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter         | Description                                                                      | Range  | Default |
+===================+==================================================================================+========+=========+
| timer-lsa-arrival | the minimum interval in which the software accepts the same link-state           | 0-1000 | 1000    |
|                   | advertisement (LSA) from OSPF neighbors                                          |        |         |
+-------------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# timers lsa-arrival 600


**Removing Configuration**

To revert to the default timer value
::

    dnRouter(cfg-protocols-ospf)# no timers lsa-arrival

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
