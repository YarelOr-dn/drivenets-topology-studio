protocols isis instance address-family ipv4-unicast microloop-avoidance fib-delay
---------------------------------------------------------------------------------

**Minimum user role:** operator

To set the required delay (in milliseconds) between the SR-TE micoloop-avoidance path installation and the post-convergance IS-IS unicast path installation:

**Command syntax: fib-delay [fib-delay]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast microloop-avoidance

**Note**

- Microloop avoidance fib-delay parameter is per IS-IS topology.

- In the event of single-topology, fib-delay of ipv4-unicast address-family will define the expected delay for ipv6 prefixes as well.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------+---------+
| Parameter | Description                                                                      | Range      | Default |
+===========+==================================================================================+============+=========+
| fib-delay | Delay time until installing post convergance IS-IS paths. Within this time       | 1000-60000 | 5000    |
|           | microloop paths will be used                                                     |            |         |
+-----------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# microloop-avoidance
    dnRouter(cfg-inst-afi-uloop)# fib-delay 10000
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# microloop-avoidance
    dnRouter(cfg-inst-afi-uloop)# fib-delay 10000


**Removing Configuration**

To revert fib-delay to the default value:
::

    dnRouter(cfg-inst-afi-uloop)# no fib-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.3    | Command introduced |
+---------+--------------------+
