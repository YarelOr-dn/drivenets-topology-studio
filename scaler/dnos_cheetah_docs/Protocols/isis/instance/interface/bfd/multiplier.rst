protocols isis instance interface bfd multiplier
------------------------------------------------

**Minimum user role:** operator

The multiplier defines the number of min-rx intervals in which a BFD packet is not received before the BFD session goes down.

To configure a local BFD multiplier:

**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface bfd

**Parameter table**

+------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter  | Description                                                                      | Range | Default |
+============+==================================================================================+=======+=========+
| multiplier | The number of min-rx intervals in which no BFD packet is received as expected    | 2-16  | 3       |
|            | (or the number of missing BFD packets) before the BFD session goes down.         |       |         |
+------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# isis-level level-1-2
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# bfd
    dnRouter(cfg-inst-if-bfd)# multiplier 5

For example, if min-rx is configured to 100 msec and the multiplier is 5, this means that if BFD packets stop arriving, after 500 msec the session goes down.


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-inst-if-bfd)# no multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
