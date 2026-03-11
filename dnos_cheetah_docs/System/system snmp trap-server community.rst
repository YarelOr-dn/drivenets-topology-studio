system snmp trap-server community
---------------------------------

**Minimum user role:** operator

To configure the SNMP trap-server community used for communicating with the remote agent:

**Command syntax: community [community-value]**

**Command mode:** config

**Hierarchies**

- system snmp trap-server

.. **Note**

	- community parameter is mandatory for snmp trap server configuration

	- Only one community can be configured per trap server

	- it is not possible to remove community configuration from trap server

	- This community field is not related to "snmp community [community-value]" command

**Parameter table**

+-----------+----------------------------------------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                                                              | Range  | Default |
+===========+==========================================================================================================+========+=========+
| community | Mandatory. The community string used to communicate with the remote agent.                               | string | \-      |
|           | Relevant only to SNMP version 1 or 2c and is mandatory. Only one community can be configured per server. |        |         |
+-----------+----------------------------------------------------------------------------------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
	dnRouter(cfg-system-snmp-trap-server)# community MySnmpCommunity 
	
	dnRouter(cfg-system-snmp)# trap-server 1.1.1.1 vrf mgmt0
	dnRouter(cfg-system-snmp-trap-server)# community MySnmpCommunity 
	
	

**Removing Configuration**

You cannot remove the community configuration. To delete the community, run the command with a new community string: 
::

	dnRouter(cfg-system-snmp-trap-server)# community MyNewSnmpCommunity

.. **Help line:** Configure system snmp trap server community

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 5.1.0   | Command introduced               |
+---------+----------------------------------+
| 6.0     | Applied new hierarchy for SNMP   |
+---------+----------------------------------+
| 9.0     | Applied new hierarchy for server |
+---------+----------------------------------+


