services twamp timers session-timeout
-------------------------------------

**Minimum user role:** operator

The session timeout parameter enable the system to clear resources, by not allowing inactive control connections or data sessions to remain available indefinitely.

-	Session-timeout - The time-frame the data session can remain inactive.

To configure the TWAMP timers:

**Command syntax: session-timeout [session-timeout]**

**Command mode:** config

**Hierarchies**

- services twamp timers

**Note**

- session-timeout and session-timeout can be set individually, together and in any order.

**Parameter table**

+-----------------+-------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                 | Range   | Default |
+=================+=============================================================+=========+=========+
| session-timeout | Length of time the session is inactive before it times out. | 60-1800 | 900     |
+-----------------+-------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)# session-timeout 900


**Removing Configuration**

To revert session-timeout to default:
::

    dnRouter(cfg-srv-twamp)# no session-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
