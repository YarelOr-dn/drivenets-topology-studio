protocols isis instance interface address-family
------------------------------------------------

**Minimum user role:** operator

This command enables the interface for the specified IS-IS address-family topology. Address-family cannot be configured if the equivalent topology isn't enabled in the IS-IS instance.
To enable an address-family on the IS-IS interface and enter address-family configuration:


**Command syntax: address-family [address-family-type]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface

**Note**
- When only IPv4-unicast is enabled for all IS-IS enabled interfaces, IS-IS works as a single topology.
- There is no default address-family. You must configure at least one address-family to enable IS-IS for the interface.
- For the ipv6-unicast address family, IS-IS metric-style must be 'wide'.


**Parameter table**

+---------------------+----------------------------------------------------------------------------------+--------------------+---------+
| Parameter           | Description                                                                      | Range              | Default |
+=====================+==================================================================================+====================+=========+
| address-family-type | The address family to be supported by the IS-IS interface. You must configure at | | ipv4-unicast     | \-      |
|                     | least one address-family to enable IS-IS on the interface.                       | | ipv6-unicast     |         |
|                     |                                                                                  | | ipv4-multicast   |         |
+---------------------+----------------------------------------------------------------------------------+--------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)#

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-multicast
    dnRouter(cfg-inst-if-afi)#

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# address-family ipv6-unicast
    dnRouter(cfg-inst-if-afi)#


**Removing Configuration**

To remove all address-family configuration:
::

    dnRouter(cfg-isis-inst-if)# no address-family

To remove a specific address-family configuration:
::

    dnRouter(cfg-isis-inst-if)# no address-family ipv4-unicast
    dnRouter(cfg-isis-inst-if)# no address-family ipv6-unicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
