protocols ospf instance area interface
--------------------------------------

**Minimum user role:** operator

To enable OSPF on an interface and enter interface OSPF configuration mode:


**Command syntax: interface [interface]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area

**Note**
- no command disables the ospf process for a specific interface.
- An interface can only be configured to a single area. when trying to configure an already in use interface to another area the following error should be displayed: "Error: unable to set interface <interface-name>. Interface attached to area < area-id >".


**Parameter table**

+-----------+------------------------+----------------------------------------+---------+
| Parameter | Description            | Range                                  | Default |
+===========+========================+========================================+=========+
| interface | ospf enabled interface | | geX-<f>/<n>/<p>                      | \-      |
|           |                        | | geX-<f>/<n>/<p>.<sub-interface-id>   |         |
|           |                        | | bundle-<bundle-id>                   |         |
|           |                        | | bundle-<bundle-id.sub-bundle-id>     |         |
|           |                        | | loX                                  |         |
|           |                        | | irb<0-65535>                         |         |
+-----------+------------------------+----------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)#
    dnRouter(cfg-protocols-ospf-area)# interface bundle-2.1012
    dnRouter(cfg-ospf-area-if)#


**Removing Configuration**

To disable authentication requirement:
::

    dnRouter(cfg-protocols-ospf-area)# no interface ge100-1/2/1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
