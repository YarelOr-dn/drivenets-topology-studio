services twamp timers server-timeout
------------------------------------

**Minimum user role:** operator

The server timeout parameter enable the system to clear resources, by not allowing inactive control connections or data sessions to remain available indefinitely.

-	Server-timeout - The time-frame to complete the control session negotiation.

To configure the TWAMP timers:

**Command syntax: server-timeout [server-timeout]**

**Command mode:** config

**Hierarchies**

- services twamp timers

**Parameter table**

+----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter      | Description                                                                      | Range   | Default |
+================+==================================================================================+=========+=========+
| server-timeout | The maximum time the Two-Way Active Measurement Protocol (TWAMP) server has to   | 60-1800 | 900     |
|                | finish the TWAMP control protocol negotiation.                                   |         |         |
+----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)# server-timeout 900


**Removing Configuration**

To revert server-timeout to default:
::

    dnRouter(cfg-srv-twamp)# no server-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
