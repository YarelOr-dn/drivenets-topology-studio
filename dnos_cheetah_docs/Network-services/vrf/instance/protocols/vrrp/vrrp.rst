network-services vrf instance protocols vrrp interface
------------------------------------------------------

**Minimum user role:** operator

To enable VRRP on an interface and enter interface configuration mode:


**Command syntax: vrrp interface [interface-name]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols
- protocols

**Parameter table**

+----------------+-----------------------------------------------------+----------------------------------------+---------+
| Parameter      | Description                                         | Range                                  | Default |
+================+=====================================================+========================================+=========+
| interface-name | The name of the interface on which VRRP is enabled. | | geX-<f>/<n>/<p>                      | \-      |
|                |                                                     | | geX-<f>/<n>/<p>.<sub-interface-id>   |         |
|                |                                                     | | bundle-<bundle-id>                   |         |
|                |                                                     | | bundle-<bundle-id.sub-bundle-id>     |         |
|                |                                                     | | irb<0-65535>                         |         |
+----------------+-----------------------------------------------------+----------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)#

    dnRouter(cfg-protocols)# vrrp interface bundle-2.1012
    dnRouter(cfg-protocols-vrrp-bundle-2.1012)#


**Removing Configuration**

To disable the VRRP process on an interface:
::

    dnRouter(cfg-protocols)# no vrrp interface ge100-0/0/0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
