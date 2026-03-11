protocols isis instance interface timers dead-interval
------------------------------------------------------

**Minimum user role:** operator

Routing devices send hello packets at a fixed interval on all interfaces to establish and maintain neighbor relationships. This interval is advertised in the dead interval field in the hello packet.

To modify the amount of time during which hello messages are missing before the neighbor can declare the adjacency as "down":


**Command syntax: dead-interval [dead-interval]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface timers

**Note**

- Reconfiguring dead-interval will reset the hello interval timer and immiditaly cause a hello message to be sent.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter     | Description                                                                      | Range   | Default |
+===============+==================================================================================+=========+=========+
| dead-interval | The dead-interval (in seconds) that will be advertised to neighbors. If a        | 1-65535 | 30      |
|               | neighbor will not receive a hello message within this interval, it will declare  |         |         |
|               | the adjacency as down.                                                           |         |         |
|               | You must select a value that is at least 3 times the value of the hello-interval |         |         |
|               | timer.                                                                           |         |         |
+---------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# timers
    dnRouter(cfg-inst-if-timers)# dead-interval 15


**Removing Configuration**

To revert to the default interval:
::

    dnRouter(cfg-inst-if-timers)# no dead-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
