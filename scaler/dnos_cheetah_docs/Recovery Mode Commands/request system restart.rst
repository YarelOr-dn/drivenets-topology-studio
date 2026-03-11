request system restart
----------------------

**Minimum user role:** admin

Use this command to do a system wide restart, or a node restart. When requesting a system-wide restart, the network interfaces on the NCPs are shut down so no further traffic can be sent or received. With the interfaces down, external devices stop forwarding traffic to the device. Then, the cluster nodes are restarted one by one.

To restart the system, use the following command.

**Command syntax: request system restart**

**Command mode:** recovery 

**Note**

- To perform a cold restart to a standby NCC, connectivity to it must be available.

.. - Request system restart performs applicative containers restart across all the system.

	- Applicative containers are Management-engine, Routing-engine, Forwarding-engine and selector.

**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+
| Parameter | Description                                                                                                                                                                                                                                             | Comment                      |
+===========+=========================================================================================================================================================================================================================================================+==============================+
| ncc-id    | Restart only the specified NCC                                                                                                                                                                                                                          | 0..1                         |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+
| ncp-id    | Restart only the specified NCP                                                                                                                                                                                                                          | 0..47                        |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+
| ncf-id    | Restart only the specified NCF                                                                                                                                                                                                                          | 0..12                        |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+
| ncm-id    | Restart only the specified NCM                                                                                                                                                                                                                          | a0, b0, a1, b1               |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+
| warm      | By default, a cold restart is done, meaning that the power is reset for all cluster elements. By specifying warm, only the DNOS software is restarted (the applicative containers: management-engine, routing-engine, forwarding-engine, and selector). | Not applicable to NCM        |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+
| force     | Remotely enforce a cold restart using IPMI connectivity.                                                                                                                                                                                                | Not applicable to NCM or NCC |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+

When the system is in recovery mode, the system restart command is used to exit recovery mode:

**Example**
::

	dnRouter(RECOVERY)# request system restart
	

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 5.1.0   | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 11.0    | Added support for all cluster elements (NCC, NCP, NCF and NCM  |
+---------+----------------------------------------------------------------+
| 11.4    | Added ability to warm restart the DNOS software.               |
+---------+----------------------------------------------------------------+
| 15.0    | Added the ability to force a cold restart to the DNOS software |
+---------+----------------------------------------------------------------+


