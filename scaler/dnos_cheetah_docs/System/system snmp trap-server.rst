system snmp trap-server
-----------------------

**Minimum user role:** operator

Configures the system snmp trap-server. The system supports up to 5 different trap-servers.
To configure the system snmp trap-server:

**Command syntax: trap-server [server-ip] vrf [vrf-name]** parameter [parameter-value]

**Removing Configuration**

**Note:**

Creation of a new snmp trap server requires configuration of server-ip & community.

vrf "default" represents the in-band management, while vrf "mgmt0" represents the out-of-band management.

Up to 5 snmp servers are allowed to be configured in total on all VRFs (mgmt0, default and non-default VRF).

snmp trap source address type will be set according to the destination server IP address type.


**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------+---------------------------+---------+
| Parameter | Description                                                                                               | Range                     | Default |
+===========+===========================================================================================================+===========================+=========+
| server-ip | Mandatory. The IP address of the SNMP server                                                              | A.B.C.D                   | \-      |
|           |                                                                                                           | x:x::x:x                  |         |
+-----------+-----------------------------------------------------------------------------------------------------------+---------------------------+---------+
| vrf-name  | Defines whether the trap-server listens to in-band or out-of-band interfaces for snmp-client get messages | default - in-band         | \-      |
|           |                                                                                                           | non-default-vrf - in-band |         |
|           |                                                                                                           | mgmt0 - out-of-band       |         |
+-----------+-----------------------------------------------------------------------------------------------------------+---------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
	dnRouter(cfg-system-snmp-trap-server)# community MySnmpCommunity 
	dnRouter(cfg-system-snmp-trap-server)# version 2c
	dnRouter(cfg-system-snmp-trap-server)# port 123

	dnRouter(cfg-system-snmp)# trap-server 2004:3221::1  vrf my_vrf
	dnRouter(cfg-system-snmp-trap-server)# community MyPrivateSnmpCommunity
	dnRouter(cfg-system-snmp-trap-server)# version 2c
	dnRouter(cfg-system-snmp-trap-server)# port 123

	dnRouter(cfg-system-snmp)# trap-server 2003:3221::1  vrf mgmt0
	dnRouter(cfg-system-snmp-trap-server)# community MyNewSnmpCommunity
	dnRouter(cfg-system-snmp-trap-server)# version 2c
	dnRouter(cfg-system-snmp-trap-server)# port 123
	
**Removing Configuration**

To remove the SNMP trap-server configuration:
::

	dnRouter(cfg-system-snmp)# no trap-server 1.2.3.4 vrf default

.. **Help line:** Configure system snmp trap server

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 5.1.0   | Command introduced                            |
+---------+-----------------------------------------------+
| 6.0     | Applied new hierarchy for SNMP                |
+---------+-----------------------------------------------+
| 9.0     | Applied new hierarchy for server              |
+---------+-----------------------------------------------+
| 10.0    | Changed syntax from "server" to "trap-server" |
+---------+-----------------------------------------------+
| 13.1    | Added trap-server out-of-band support         |
+---------+-----------------------------------------------+
| 15.1    | Added support for IPV6 address format         |
+---------+-----------------------------------------------+
