network-services vpws instance interface
----------------------------------------

**Minimum user role:** operator

To configure an interface to use the VPWS service, also known as the Attachment-Circuit. This can be any in-band interface, such as physical, sub-interface, bundle, or breakout interface.

The Pseudowire type is defined by default according to the AC interface type:
- physical interface will result in PW type Ethernet (type 5)
- sub-interface type vlan will result in PW type Vlan (type 4)
- sub-interface type untagged will result in PW type Ethernet (type 5)

Packets received on PW to be sent from AC:
- for AC vlan - by default, update packet tagging to match AC tag
- for AC vlan - by default, packet is sent without any modifications

**Command syntax: interface [interface]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance

**Note**

- Only interface types <geX-X/X/X/bundle-X/<geX-X/X/X.Y>/<bundle-X.Y> are supported.

- The Pseudowire is not established until the interface is configured.

- The interface must be a L2-service enabled interface.

- The interface cannot be assign to multiple services.

**Parameter table**

+-----------+-------------------------------------+------------------+---------+
| Parameter | Description                         | Range            | Default |
+===========+=====================================+==================+=========+
| interface | the vpws service attachment circuit | | string         | \-      |
|           |                                     | | length 1-255   |         |
+-----------+-------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# interface ge100-0/0/0

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# VPWS_1
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)#  interface bundle-1

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# VPWS_1
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# interface ge100-0/0/0.1


**Removing Configuration**

To remove the interface configuration:
::

    dnRouter(cfg-network-services-vpws-inst)# no interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
