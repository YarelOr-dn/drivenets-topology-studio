protocols bfd
-------------

**Minimum user role:** operator

To start the BFD process and enter BFD configuration mode:

**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The BFD protocol is only relevant for default vrf

.. - The no command returns bfd setting to their default value

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bfd
	dnRouter(cfg-protocols-bfd)#

**Removing Configuration**

To disable the BFD protocol:
::

	dnRouter(cfg-protocols)# no bfd

.. **Help line:** Configure BFD protocol

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
