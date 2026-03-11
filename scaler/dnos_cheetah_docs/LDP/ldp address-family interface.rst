ldp address-family interface
----------------------------

**Minimum user role:** operator

To enable LDP on an interface for a specified address-family and entering LDP interface configuration mode:

**Command syntax: interface [interface-name]**

**Command mode:** config

**Hierarchies**

- protocols ldp address-family

**Note**

- Notice the change in prompt.

- This cannot be set on a Loopback interface.

**Parameter table**

+-------------------+--------------------------------------------------------------+----------------------------------------------------+-------------+
|                   |                                                              |                                                    |             |
| Parameter         | Description                                                  | Range                                              | Default     |
+===================+==============================================================+====================================================+=============+
|                   |                                                              |                                                    |             |
| interface-name    |  The name of the interface on which LDP is to be enabled.    | ge{/10/25/40/100}-X/Y/Z                            | \-          |
|                   |                                                              |                                                    |             |
|                   |                                                              | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |             |
|                   |                                                              |                                                    |             |
|                   |                                                              | bundle-<bundle-id>                                 |             |
|                   |                                                              |                                                    |             |
|                   |                                                              | bundle-<bundle-id.subinterface>                    |             |
+-------------------+--------------------------------------------------------------+----------------------------------------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# interface ge100-1/2/1
	dnRouter(cfg-protocols-ldp-afi-if)#

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# interface bundle-2
	dnRouter(cfg-protocols-ldp-if)#

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp)# interface bundle-2.1012
	dnRouter(cfg-protocols-ldp-if)#

**Removing Configuration**

To disable the LDP process for all interfaces:
::

	dnRouter(cfg-protocols-ldp)# no interface

To disable the LDP process for a specific interface:
::

	dnRouter(cfg-protocols-ldp)# no interface ge100-1/2/1

.. **Help line:** Enables LDP on an interface for the specified address-family, then enters ldp interface configuration

**Command History**

+-------------+----------------------------------------------+
|             |                                              |
| Release     | Modification                                 |
+=============+==============================================+
|             |                                              |
| 6.0         | Command introduced                           |
+-------------+----------------------------------------------+
|             |                                              |
| 13.0        | Updated range values for interface-name      |
+-------------+----------------------------------------------+