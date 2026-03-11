system aaa-server radius server 
-------------------------------

**Minimum user role:** operator

To define a remote RADIUS server and enter its configuration mode:

**Command syntax: radius server priority [priority] address [address] vrf [vrf-name]** parameters [parameters]

**Command mode:** config

**Hierarchies**

- system aaa-server radius server


**Note**

- Notice the change in prompt.

- You can configure up to 5 RADIUS servers.

.. - Up to 5 in-band (vrf default) and 5 out-of-band (vrf mgmt0) RADIUS servers are supported

	- Out-of-band packets will be sent with mgmt0 ip address.

	- Source IP address family will be matching the destination IP address family, both IPv6 or IPv4.

	- Changing address per specific priority changes only the address configuration, all other configurations remain intact

	- "no radius server priority [priority]" removes the RADIUS server configuration


**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+---------+
| Parameter | Description                                                                                                                                                           | Range                   | Default |
+===========+=======================================================================================================================================================================+=========================+=========+
| priority  | The priority level of the RADIUS server. When multiple servers are configured, the server with the higher priority (lower configured number) will be attempted first. | 1..255 characters       | \-      |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+---------+
| address   | The IP address of the RADIUS server.                                                                                                                                  | IPv4 address (A.B.C.D)  | \-      |
|           | Changing the address for a specific priority, changes only the address configuration. All other configurations remain intact.                                         | IPV6 address (x:x::x:x) |         |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+---------+
| vrf-name  | Defines server management via in-band or out-of-band                                                                                                                  | default (in-band)       | \-      |
|           |                                                                                                                                                                       | mgmt0 (OOB)             |         |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius
	dnRouter(cfg-system-aaa-radius)# server priority 1 address 192.168.1.1
	dnRouter(cfg-aaa-radius-server)# vrf default
	dnRouter(cfg-aaa-radius-server)# password enc-!@#$%
	dnRouter(cfg-aaa-radius-server)# authenticaion enabled
	dnRouter(cfg-aaa-radius-server)# port 100
	dnRouter(cfg-aaa-radius-server)# retries 3
	dnRouter(cfg-aaa-radius-server)# retry-interval 20
	dnRouter(cfg-system-aaa-radius)# server priority 2 address 192.168.1.2
	dnRouter(cfg-aaa-radius-server)# vrf mgmt0
	dnRouter(cfg-aaa-radius-server)# password enc-!@#$%
	dnRouter(cfg-aaa-radius-server)# authenticaion enabled	
	dnRouter(cfg-aaa-radius-server)# port 100
	dnRouter(cfg-aaa-radius-server)# retries 5
	dnRouter(cfg-aaa-radius-server)# retry-interval 15
	dnRouter(cfg-system-aaa-radius)# server priority 5 address 1134:1134::1
	dnRouter(cfg-aaa-radius-server)# vrf mgmt0
	dnRouter(cfg-aaa-radius-server)# password enc-!@#$%
	dnRouter(cfg-aaa-radius-server)# authenticaion enabled
	dnRouter(cfg-aaa-radius-server)# port 100
	dnRouter(cfg-aaa-radius-server)# retries 5
	dnRouter(cfg-aaa-radius-server)# retry-interval 15
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-aaa)# no radius server priority 1


.. **Help line:** Configure RADIUS server

**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 13.0    | Command introduced                           |
+---------+----------------------------------------------+
| 13.1    | Added support for OOB management (VRF mgmt0) |
+---------+----------------------------------------------+
| 15.1    | Added support for IPv6 address format        |
+---------+----------------------------------------------+


