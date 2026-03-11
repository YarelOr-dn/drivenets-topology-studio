protocols ospf instance area interface delay-normalization interval
-------------------------------------------------------------------

**Minimum user role:** operator

To configure the OSPFv2 delay normalization interval on the interface:


**Command syntax: interval [delay-normalization-interval]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface delay-normalization

**Parameter table**

+------------------------------+----------------------------------------------------------------+--------------+---------+
| Parameter                    | Description                                                    | Range        | Default |
+==============================+================================================================+==============+=========+
| delay-normalization-interval | The value of the delay normalization interval in microseconds. | 1-4294967295 | \-      |
+------------------------------+----------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area
    dnRouter(cfg-protocols-ospf-area)# interface ge100-0/0/0
    dnRouter(cfg-ospf-area-interface)# delay-normalization
    dnRouter(cfg-area-interface-normalization)# interval 5


**Removing Configuration**

To remove the delay normalization interval configuration:
::

    dnRouter(cfg-area-interface-normalization)# no interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
