protocols ospfv3 area interface
-------------------------------

**Minimum user role:** operator

To enable OSPFV3 on an interface and enter interface OSPFV3 configuration mode:


**Command syntax: interface [interface]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area

**Note**
- The 'no' command disables the ospfv3 process for a specific interface.
- An interface can only be configured to a single area. when trying to configure an already in use interface to another area the following error should be displayed: "Error: unable to set interface <interface-name>. Interface attached to area < area-id >".


**Parameter table**

+-----------+--------------------------+----------------------------------------+---------+
| Parameter | Description              | Range                                  | Default |
+===========+==========================+========================================+=========+
| interface | ospfv3 enabled interface | | geX-<f>/<n>/<p>                      | \-      |
|           |                          | | geX-<f>/<n>/<p>.<sub-interface-id>   |         |
|           |                          | | bundle-<bundle-id>                   |         |
|           |                          | | bundle-<bundle-id.sub-bundle-id>     |         |
|           |                          | | loX                                  |         |
|           |                          | | irb<0-65535>                         |         |
+-----------+--------------------------+----------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-1/2/1
    dnRouter(cfg-ospfv3-area-if)#
    dnRouter(cfg-protocols-ospfv3-area)# interface bundle-2.1012
    dnRouter(cfg-ospfv3-area-if)#


**Removing Configuration**

To disable authentication requirement:
::

    dnRouter(cfg-protocols-ospfv3-area)# no interface ge100-1/2/1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
