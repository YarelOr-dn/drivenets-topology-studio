show system snmp summary
------------------------

**Minimum user role:** viewer

The following command displays the SNMP configuration, including communities (see show system snmp communities), servers (see show system snmp trap-servers), and traps status (see show system snmp traps):

**Command syntax: show system snmp summary**

**Command mode:** operational



.. **Internal Note**

	- System snmp engineID defined according RFC 3411, first 4 bytes for IANA assigned (49739), 5  :sup:`th` byte 0, rest of bytes (6-12) are randomly generated once system start-up (saved in Redis)


**Example**
::

	dnRouter# show system snmp summary

	SNMP engineID: 0000c24b00deda235381a6b2
	Class-of-service: 16
	Source-interface: lo10

	SNMP Communities:

	| Community               | VRF        | Admin-State |Access     | View         | Clients                           |
	|-------------------------+------------+-------------+-----------+--------------+-----------------------------------|
	| MyPublicSnmpCommunity   | default    | enabled     | read-only | MySnmpView1  | 192.168.1.0/24 , 172.17.0.1/32    |
	| MyPrivateSnmpCommunity  | default    | enabled     | read-write| MySnmpView1  |                                   |
	| TestCommunity           | mgmt0      | disabled    | read-only | viewdefault  | 192.192.100.1/32, 2.2.2.0/24      |
	| MySnmpCommunity         | my_vrf     | enabled     | read-only | MySnmpView1  | 172.17.1.0/16, 2001:db8:3333::/48 |

	SNMP Trap-Servers:

	| VRF        | Admin-State | Server       | Port  | Version | Security      | Community              |
	|------------+-------------+--------------+-------+---------+---------------+------------------------|
	| default    | enabled     | 1.2.3.4      | 162   | 1       | none          | MySnmpCommunity        |
	| mgmt0      | enabled     | 192.168.1.1  | 162   | 2c      | none          | MySnmpCommunity        |
	| my_vrf     | disabled    | 2004:3221::1 | 162   | 2c      | none          | MyPrivateSnmpCommunity |

	SNMP Trap List:

	| Trap             | Status     |
	|------------------+------------|
	| snmp-linkup      | enabled    |
	| snmp-linkdown    | disabled   |
	| snmp-coldstart   | enabled    |

	SNMP Users:

	| User          | Authentication | Encryption | View        |
	|---------------+----------------+------------+-------------|
	| MySnmpUserv1  | md5            | none       | viewdefault |
	| MySnmpUserv2  | none           | none       | viewdefault |
	| MySnmpUserv3  | sha            | des        | viewall     |

	SNMP mibs:

	| OID                          | Object Name                  |
	|------------------------------|------------------------------|
	| 1.3.6.1.2.1.11.1             | snmp.1                       |
	| 1.3.6.1.4.1.99.12.35.1.1.1.1 | enterprises.99.12.35.1.1.1.1 |
	| 1.3.6.1.6.3.1.1.6.1          | internet.3.6.1.6.3.1.1.6.1   |

	SNMP views:

	View: viewdefault
	Include: iso.
	Exclude: snmp.1
	 snmp.2
	 1.2.3.4.5.7
	 1.1.6.3.1.2.5
	 internet.2

	View: viewall
	Include: iso.
		 snmp.3
		 snmp.4
	Exclude: snmp.1
	 snmp.2
	 1.2.3.4.5.7
	 1.1.6.3.1.2.5
	 internet.2


.. **Help line:** show system snmp summary

**Command History**

+---------+-----------------------------------------------------------------------------------+
| Release | Modification                                                                      |
+=========+===================================================================================+
| 5.1.0   | Command introduced                                                                |
+---------+-----------------------------------------------------------------------------------+
| 6.0     | Updated the example -displaying user, mibs and views                              |
+---------+-----------------------------------------------------------------------------------+
| 11.0    | Added "class-of-service" and "source-interface" to the output                     |
+---------+-----------------------------------------------------------------------------------+
| 13.1    | Added in-band (default VRF) / out-of-band (mgmt0 VRF) configuration per community |
+---------+-----------------------------------------------------------------------------------+
| 16.1    | Added Admin-State field to Communities and Trap-Servers                           |
+---------+-----------------------------------------------------------------------------------+

