protocols ospf instance area interface dead-interval
----------------------------------------------------

**Minimum user role:** operator

To configure the amount of time to wait for a hello-packet from the neighbor before declaring that neighbor dead:

**Command syntax: dead-interval [dead-interval]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**
- If the hello-interval was set (see "ospf area interface hello-interval"), the dead-interval should be four times bigger than the hello-interval.
- no command sets the dead interval to its default value.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter     | Description                                                                      | Range   | Default |
+===============+==================================================================================+=========+=========+
| dead-interval | Dead interval:  this defines how long (in seconds) we should wait for hello      | 1-65535 | 40      |
|               | packets before we declare the neighbor dead                                      |         |         |
+---------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# dead-interval 120


**Removing Configuration**

To return the dead interval to its default value:
::

    dnRouter(cfg-protocols-ospf-area)# interface ge100-2/1/1

::

    dnRouter(cfg-ospf-area-if)# no dead-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
