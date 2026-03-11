protocols isis instance interface timers hello-interval
-------------------------------------------------------

**Minimum user role:** operator

Routing devices send hello packets at a fixed interval on all interfaces to establish and maintain neighbor relationships. This interval is advertised in the hello interval field in the hello packet.

To modify the frequency with which the routing device sends hello packets out of an interface:


**Command syntax: hello-interval [hello-interval]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface timers

**Note**

- Reconfiguring hello-interval will reset the interval timer and immiditaly cause a hello message to be sent.

**Parameter table**

+----------------+------------------------------------------------------------+---------+---------+
| Parameter      | Description                                                | Range   | Default |
+================+============================================================+=========+=========+
| hello-interval | The time (in seconds) between hello messages for a domain. | 1-65535 | 10      |
+----------------+------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# timers
    dnRouter(cfg-inst-if-timers)# hello-interval 5


**Removing Configuration**

To revert to the default interval:
::

    dnRouter(cfg-inst-if-timers)# no hello-interval

**Command History**

+---------+----------------------+
| Release | Modification         |
+=========+======================+
| 6.0     | Command introduced   |
+---------+----------------------+
| 9.0     | Command removed      |
+---------+----------------------+
| 10.0    | Command reintroduced |
+---------+----------------------+
