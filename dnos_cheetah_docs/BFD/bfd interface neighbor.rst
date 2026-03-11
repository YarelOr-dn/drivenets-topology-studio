bfd interface neighbor
----------------------

**Minimum user role:** operator

You must set a destination address for the uBFD session. The destination address does not need to be an IP address of the interface you want to protect; it can also be a loopback address, as long as it is a local address of the router that will cause the BFD packets to trap to the CPU.

To set the destination address for the uBFD session:


**Command syntax: neighbor [ip-address]**

**Command mode:** config

**Hierarchies**

- protocols bfd  

**Note**

- User must set neighbor address in order for the micro BFD sessions to work (commit failure)

- Neighbor address-family type must match local-address address family type

- Only a single neighbor address can be configured per a bundle interface

- BFD session address-family match the neighbor address-family.

.. no command removes neighbor address and stop BFD session


**Parameter table**

+---------------+-------------------------------------------------------------------------------------------------------+-------------+-------------+
|               |                                                                                                       |             |             |
| Parameter     | Description                                                                                           | Range       | Default     |
+===============+=======================================================================================================+=============+=============+
|               |                                                                                                       |             |             |
| ip-address    | The IPv4/IPv6 address of the neighbor at the remote end of the bundle interface for the uBFD session. | A.B.C.D     | \-          |
|               |                                                                                                       |             |             |
|               |                                                                                                       | x:x::x:x    |             |
+---------------+-------------------------------------------------------------------------------------------------------+-------------+-------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bfd
	dnRouter(cfg-protocols-bfd)# interface bundle-1
	dnRouter(cfg-protocols-bfd-if)# neighbor 1.2.3.4
	
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bfd
	dnRouter(cfg-protocols-bfd)# interface bundle-1
	dnRouter(cfg-protocols-bfd-if)# neighbor 2001:ab12::2
	
	

**Removing Configuration**

To remove the neighbor address and stop the BFD session: 
::

	dnRouter(cfg-protocols-bfd-if)# no neighbor


**Command History**

+-------------+-------------------------------------+
|             |                                     |
| Release     | Modification                        |
+=============+=====================================+
|             |                                     |
| 11.2        | Command introduced                  |
+-------------+-------------------------------------+
