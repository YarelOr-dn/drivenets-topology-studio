request system restart
----------------------

**Minimum user role:** admin

Use this command to do a system wide restart, or a node restart. When requesting a system-wide restart, the network interfaces on the NCPs are shut down so no further traffic can be sent or received. With the interfaces down, external devices stop forwarding traffic to the device. Then, the cluster nodes are restarted one by one.

When the system is in recovery mode, the system restart command is used to exit recovery mode. This will restart all the system containers (management engine, forwarding engine, routing engine, and selector). You will be prompted to confirm the action. If you are sure you want to restart the system, type ‘yes’.

To restart the system, use the following command. 

**Command syntax: request system restart** {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-id]} warm force

**Command mode:** operational

**Note**

- To perform a cold restart to a standby NCC, connectivity to it must be available.

..
	**Internal Note**

	-  Yes/no validation should exist for system restart operation.

	-  Request system restart warm performs applicative containers restart across all the system.

	   -  Applicative containers are Management-engine, Routing-engine, Forwarding-engine and selector.

	-  For "request system restart warm" NCM will not reset. Cannot choose warm restart for node type of ncm

**Parameter table**

+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
|               |                                                                                                                                                                                                                                                                  |                                 |
| Parameter     | Description                                                                                                                                                                                                                                                      | Comment                         |
+===============+==================================================================================================================================================================================================================================================================+=================================+
|               |                                                                                                                                                                                                                                                                  |                                 |
| ncc-id        | Restart only the specified NCC                                                                                                                                                                                                                                   | 0..1                            |
+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
|               |                                                                                                                                                                                                                                                                  |                                 |
| ncp-id        | Restart only the specified NCP                                                                                                                                                                                                                                   | 0..47                           |
+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
|               |                                                                                                                                                                                                                                                                  |                                 |
| ncf-id        | Restart only the specified NCF                                                                                                                                                                                                                                   | 0..12                           |
+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
|               |                                                                                                                                                                                                                                                                  |                                 |
| ncm-id        | Restart only the specified NCM                                                                                                                                                                                                                                   | a0, b0, a1, b1                  |
+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
|               |                                                                                                                                                                                                                                                                  |                                 |
| warm          | By default, a cold restart is done, meaning that   the power is reset for all cluster elements. By specifying warm, only the   DNOS software is restarted (the applicative containers: management-engine,   routing-engine, forwarding-engine, and selector).    | Not applicable to NCM           |
+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
|               |                                                                                                                                                                                                                                                                  |                                 |
| force         | Remotely enforce a cold restart using IPMI   connectivity.                                                                                                                                                                                                       | Not applicable to NCM or NCC    |
+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+

**Example**
::

	dnRouter# request system restart
	Warning: Are you sure you want to perform a system restart? (Yes/No) [No]? 
	
	dnRouter# request system restart warm
	Warning: Are you sure you want to perform a system restart? (Yes/No) [No]? 
	
	dnRouter# request system restart ncc 1
	Warning: Are you sure you want to perform a system restart? (Yes/No) [No]? 
	
	dnRouter# request system restart ncp 3 warm
	Warning: Are you sure you want to perform a system restart? (Yes/No) [No]? 
	
	dnRouter# request system restart ncm a1
	Warning: Are you sure you want to perform a system restart? (Yes/No) [No]? 

	dnRouter# request system restart ncp 0 force
	Warning: Are you sure you want to perform a system restart? (Yes/No) [No]? 
	

.. **Help line:**

**Command History**

+-------------+---------------------------------------------------------------------+
|             |                                                                     |
| Release     | Modification                                                        |
+=============+=====================================================================+
|             |                                                                     |
| 5.1.0       | Command introduced                                                  |
+-------------+---------------------------------------------------------------------+
|             |                                                                     |
| 11.0        | Added support for all cluster elements (NCC, NCP,   NCF and NCM     |
+-------------+---------------------------------------------------------------------+
|             |                                                                     |
| 11.4        | Added ability to warm restart the DNOS software.                    |
+-------------+---------------------------------------------------------------------+
|             |                                                                     |
| 15.0        | Added the ability to force a cold restart to the   DNOS software    |
+-------------+---------------------------------------------------------------------+