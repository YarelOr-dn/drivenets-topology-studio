protocols pim hello-interval
----------------------------

**Minimum user role:** operator

The graceful restart time is the time limit to maintain stale PIM-originated multicast forwarding entries before they are cleared. Multicast forwarding entries become stale following a PIM process restart (for example, following a restart of the routing engine or a cluster NCC failover event). After the grace time, all stale PIM join/prune states are discarded and the related multicast RIB and FIB entries are removed.

To configure the PIM graceful restart timeout:

**Command syntax: hello-interval [hello-interval]**

**Command mode:** config

**Hierarchies**

- protocols pim

**Note**
- Any change in the pim hello interval will take effect immediately if the new value is lower than the previous value. Otherwise, it will only take effect after the derived timers, such as PIM hello hold-time, are updated and sent to peer routers at least once.

- The derived hello hold-time is 3.5 x hello-interval and it must be greater than the graceful-restart-time.

**Parameter table**

+----------------+--------------------------------------+--------+---------+
| Parameter      | Description                          | Range  | Default |
+================+======================================+========+=========+
| hello-interval | Periodic interval for Hello messages | 1-3600 | 30      |
+----------------+--------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# hello-interval 100
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no hello-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
