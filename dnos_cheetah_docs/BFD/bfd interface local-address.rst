bfd interface local-address
---------------------------

**Minimum user role:** operator

To set the local address to be used as the IP source of uBFD sessions:

**Command syntax: local-address [ip-address]**

**Command mode:** config

**Hierarchies**

- protocols bfd  

**Note**

- The local address-family type must match the neighbor address address-family type

.. - no command returns local-address to default value


**Parameter table**

+---------------+----------------------------------------------------------------------------+-------------+------------------------------------+
|               |                                                                            |             |                                    |
| Parameter     | Description                                                                | Range       | Default                            |
+===============+============================================================================+=============+====================================+
|               |                                                                            |             |                                    |
| ip-address    | The local address that will be used as the IP source for uBFD sessions.    |  A.B.C.D    | The IP address of the interface    |
|               |                                                                            |             |                                    |
|               |                                                                            | x:x::x:x    |                                    |
+---------------+----------------------------------------------------------------------------+-------------+------------------------------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bfd
	dnRouter(cfg-protocols-bfd)# interface bundle-1
	dnRouter(cfg-protocols-bfd-if)# local-address 1.2.3.3
	
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bfd
	dnRouter(cfg-protocols-bfd)# interface bundle-1
	dnRouter(cfg-protocols-bfd-if)# local-address 2001:ab12::2
	
	

**Removing Configuration**

To remove BFD support for a specific address-family: 
::

	dnRouter(cfg-protocols-bfd-if)# no local-address


**Command History**

+-------------+-------------------------------------+
|             |                                     |
| Release     | Modification                        |
+=============+=====================================+
|             |                                     |
| 11.2        | Command introduced                  |
+-------------+-------------------------------------+
