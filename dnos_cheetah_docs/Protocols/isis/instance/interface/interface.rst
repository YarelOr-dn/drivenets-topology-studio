protocols isis instance interface
---------------------------------

**Minimum user role:** operator

To enable IS-IS on an interface and enter interface configuration mode:


**Command syntax: interface [interface-name]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- Loopback interfaces can be set on multiple IS-IS instances. All other interface types cannot be enabled on more than one IS-IS instance. Loopback interfaces are passive by default.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+----------------------------------------+---------+
| Parameter      | Description                                                                      | Range                                  | Default |
+================+==================================================================================+========================================+=========+
| interface-name | The name of the interface on which IS-IS is enabled. An interface can only be    | | configured interface name.           | \-      |
|                | configured to a single IS-IS instance.                                           | | lo<0-65535>                          |         |
|                |                                                                                  | | irb<0-65535>                         |         |
|                |                                                                                  | | ge{/10/25/40/100}-X/Y/Z              |         |
|                |                                                                                  | | geX-<f>/<n>/<p>.<sub-interface id>   |         |
|                |                                                                                  | | bundle-<bundle-id>                   |         |
|                |                                                                                  | | bundle-<bundle-id.sub-bundle-id>     |         |
|                |                                                                                  | | gre-tunnel-<id>                      |         |
+----------------+----------------------------------------------------------------------------------+----------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface ge100-1/2/1
    dnRouter(cfg-isis-inst-if)#

    dnRouter(cfg-protocols-isis-inst)# interface bundle-2.1012
    dnRouter(cfg-isis-inst-if)#

    dnRouter(cfg-protocols-isis-inst)# interface gre-tunnel-0
    dnRouter(cfg-isis-inst-if)#


**Removing Configuration**

To disable the IS-IS process on an interface:
::

    dnRouter(cfg-protocols-isis-inst)# no interface ge100-1/2/1

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 6.0     | Command introduced            |
+---------+-------------------------------+
| 11.4    | Added support for GRE-tunnels |
+---------+-------------------------------+
