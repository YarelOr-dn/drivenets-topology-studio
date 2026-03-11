traffic-engineering interface
-----------------------------

**Minimum user role:** operator

To enable MPLS traffic engineering on an interface and enter its configuration mode:

**Command syntax: interface [interface-name]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering

**Note**

- The command is applicable to the following interface types:

	- Physical

	- Physical vlan

	- Bundle

	- Bundle vlan

- You must enable both RSVP and MPLS TE on an interface for the system to be able to establish an RSVP session and an LSP through the interface.

- Removing the interface configuration will cause the interface to be removed from the IGP TE database.


**Parameter table**

+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+---------+
|                   |                                                                                                                                                                                                |                                                       |         |
| Parameter         | Description                                                                                                                                                                                    | Range                                                 | Default |
+===================+================================================================================================================================================================================================+=======================================================+=========+
|                   |                                                                                                                                                                                                |                                                       |         |
| interface-name    | The name of the interface on which to enable TE.   This enables the interface for RSVP signaling and also enables to advertise   the IGP-TE database, if TE is enabled in the IGP protocol.    | configured interface name.                            |   \-    |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                | ge{/10/25/40/100}-X/Y/Z                               |         |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                | ge<interface speed>-<A>/<B>/<C>.<sub-interface   id>  |         |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                | bundle-<bundle-id>                                    |         |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                |                                                       |         |
|                   |                                                                                                                                                                                                | bundle-<bundle-id.sub-bundle-id>                      |         |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# interface bundle-1
	dnRouter(cfg-mpls-te-if)#

**Removing Configuration**

To remove the MPLS TE interface configuration:
::

	dnRouter(cfg-protocols-mpls-te)#  no interface bundle-1


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 9.0         | Command introduced    |
+-------------+-----------------------+