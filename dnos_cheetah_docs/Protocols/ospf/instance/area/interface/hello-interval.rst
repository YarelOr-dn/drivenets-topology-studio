protocols ospf instance area interface hello-interval
-----------------------------------------------------

**Minimum user role:** operator

To configure the frequency of sending hello packets:

**Command syntax: hello-interval [hello-interval]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**
- If dead-interval was set (see "ospf area interface dead-interval"), hello interval should be four times smaller than the dead-interval.
- No command sets the hello interval to its default value.

**Parameter table**

+----------------+------------------------------------------------------------------------------+---------+---------+
| Parameter      | Description                                                                  | Range   | Default |
+================+==============================================================================+=========+=========+
| hello-interval | Hello interval: this defines how often (in seconds) we send the hello packet | 1-16383 | 10      |
+----------------+------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# hello-interval 200


**Removing Configuration**

To return the hello interval to its default value:
::

    dnRouter(cfg-protocols-ospf-area)# interface ge100-2/1/1

::

    dnRouter(cfg-ospf-area-if)# no hello-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
