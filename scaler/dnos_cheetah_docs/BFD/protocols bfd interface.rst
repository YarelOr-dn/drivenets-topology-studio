protocols bfd interface
-----------------------

**Minimum user role:** operator

To configure BFD on an interface:

**Command syntax: interface [interface-name]**

**Command mode:** config

**Hierarchies**

- protocols bfd

**Note**

- This command applies to bundle interfaces only.

- BFD session configurations applies to all bundle member sessions.

- micro-BFD will work on the vrf to which the bundle interface is assigned. If the bundle interface switches between different vrfs, the micro-bfd session will close and reopen.

.. - 'no interface bundle-1' - remove interface bundle-1 bfd configurations

.. - 'no interface' - remove all interfaces bfd configurations



**Parameter table**

+-------------------+--------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------------+
|                   |                                                                                                                                            |                      |                   |
| Parameter         | Description                                                                                                                                | Value                | Default value     |
+===================+============================================================================================================================================+======================+===================+
|                   |                                                                                                                                            |                      |                   |
| interface-name    | The name of the interface on which to configure BFD.                                                                                       | bunde-<bundle-id>    | \-                |
|                   |                                                                                                                                            |                      |                   |
|                   | For uBFD to work, the bundle interface must have an IP address and the packets' destination-ip must match any interface in the system.     |                      |                   |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bfd
	dnRouter(cfg-protocols-bfd)# interface bundle-1
	dnRouter(cfg-protocols-bfd-if)#


**Removing Configuration**

To remove the interface bfd configuration:
::

	dnRouter(cfg-protocols-bfd)# no interface bundle-1
	dnRouter(cfg-protocols-bfd)# no interface


**Command History**

+-------------+-------------------------+
|             |                         |
| Release     | Modification            |
+=============+=========================+
|             |                         |
| 6.0         | Command introduced      |
+-------------+-------------------------+
|             |                         |
| 9.0         | Command removed         |
+-------------+-------------------------+
|             |                         |
| 11.2        | Command reintroduced    |
+-------------+-------------------------+