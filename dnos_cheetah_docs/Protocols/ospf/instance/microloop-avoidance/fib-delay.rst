protocols ospf instance microloop-avoidance fib-delay
-----------------------------------------------------

**Minimum user role:** operator

To set the required delay (in milliseconds) between the SR-TE micoloop-avoidance path installation and the post-convergance OSPF unicast path installation:

**Command syntax: fib-delay [fib-delay]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance microloop-avoidance

**Note**

- Microloop avoidance fib-delay parameter is per OSPF topology.

- The fib-delay timer should be configured to a value that corresponds to the worst-case IGP convergence in a given network domain.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------+---------+
| Parameter | Description                                                                      | Range      | Default |
+===========+==================================================================================+============+=========+
| fib-delay | Delay time until installing post convergance OSPFv2 paths. Within this time      | 1000-60000 | 5000    |
|           | microloop paths will be used                                                     |            |         |
+-----------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance INSTANCE_1
    dnRouter(cfg-protocols-ospf-inst)# microloop-avoidance
    dnRouter(cfg-ospf-inst-uloop)# fib-delay 10000


**Removing Configuration**

To revert fib-delay to the default value:
::

    dnRouter(cfg-ospf-inst-uloop)# no fib-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
