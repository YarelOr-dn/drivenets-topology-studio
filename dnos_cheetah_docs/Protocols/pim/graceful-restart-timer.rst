protocols pim graceful-restart-timer
------------------------------------

**Minimum user role:** operator

The graceful restart time is the time limit to maintain stale PIM-originated multicast forwarding entries before they are cleared. Multicast forwarding entries become stale following a PIM process restart (for example, following a restart of the routing engine or a cluster NCC failover event). After the grace time, all stale PIM join/prune states are discarded and the related multicast RIB and FIB entries are removed.

To configure the PIM graceful restart timeout:

**Command syntax: graceful-restart-timer [graceful-restart-timer]**

**Command mode:** config

**Hierarchies**

- protocols pim

**Note**
- The graceful restart time must be lower than the hello-holdtime, or lower than the maximum interface hello-interval times 3.5 seconds to ensure non-stop routing with all peer PIM neighbors.

- In the event that PIM NSR is enabled, its timer shall be used instead of the configured PIM graceful restart time.

**Parameter table**

+------------------------+----------------------------------------------+---------+---------+
| Parameter              | Description                                  | Range   | Default |
+========================+==============================================+=========+=========+
| graceful-restart-timer | Maximum time for graceful restart to finish. | 30-3600 | 90      |
+------------------------+----------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# graceful-restart-time 100
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no graceful-restart-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
