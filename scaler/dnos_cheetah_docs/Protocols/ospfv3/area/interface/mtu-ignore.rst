protocols ospfv3 area interface mtu-ignore
------------------------------------------

**Minimum user role:** operator

To disable the MTU mismatch detection:

**Command syntax: mtu-ignore**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area interface

**Note**

- The MTU-ignore is disabled by default.

- no MTU-ignore - returns the MTU mismatch detection.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-1/2/1
    dnRouter(cfg-ospfv3-area-if)# mtu-ignore


**Removing Configuration**

To return the mtu mismatch to its default value: 
::

    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-2/1/1

::

    dnRouter(cfg-ospfv3-area-if)# no mtu-ignore

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
