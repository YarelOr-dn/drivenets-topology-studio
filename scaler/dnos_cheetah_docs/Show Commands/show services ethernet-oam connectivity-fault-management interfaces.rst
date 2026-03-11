show services ethernet-oam connectivity-fault-management interfaces
-------------------------------------------------------------------

**Minimum user role:** viewer

To display information for Connectivity Fault Management interfaces:


**Command syntax: show services ethernet-oam connectivity-fault-management interfaces** {[interface-name] | all}

**Command mode:** operational

..
	**Internal Note**
	
	-  

**Example**
::

	dnRouter# show services ethernet-oam connectivity-fault-management interfaces

	Connectivity Fault Management Ethernet OAM interfaces summary:

	Defects: X - DefXconCCM, E - DefErrorCCM, L - DefRemoteCCM, M - DefMACstatus, R - DefRDICCM

	Local MEPs:
	+---------------+----------+--------------+---------------------+-----------+-----------+-------------+--------------+-----------+-------------------+
	| Interface     | MD level | MD name      | MA name             | MEP-ID    | Direction | Admin State | CCM TX State | Defects   | MAC Address       |
	+===============+==========+==============+=====================+===========+===========+=============+==============+===========+===================+
	| bundle-1.2001 | 0        | MD0_LEVEL0   | BD_CFM2001_PE-to-CE | 1         | down      | enabled     | enabled      | R         | 7c:fe:90:57:73:10 |
	|               | 4        | MD4_LEVEL4   | BD_CFM2001_PE-to-PE | 38        | up        | enabled     | enabled      | L         | 7c:fe:90:57:73:13 |
	+---------------+----------+--------------+---------------------+-----------+-----------+-------------+--------------+-----------+-------------------+

	Local MIPs:
	+---------------+----------+--------------+---------------------+-----------+-------------+-------------------+
	| Interface     | MD level | MD name      | MA name             | MIP name  | Admin State |  MAC Address      |
	+===============+==========+==============+=====================+===========+===========+=====================+
	| bundle-1.2001 | 0        | MD0_LEVEL0   | BD_CFM2001_PE-to-CE | My_MIP1   | enabled     | 7c:fe:90:57:73:10 |
	|               | 4        | MD4_LEVEL4   | BD_CFM2001_PE-to-PE | My_MIP2   | enabled     | 7c:fe:90:57:73:13 |
	+---------------+----------+--------------+---------------------+-----------+-------------+-------------------+


	dnRouter# show services ethernet-oam connectivity-fault-management interfaces bundle-1.2001

	Connectivity Fault Management Ethernet OAM interface bundle-1.2001:

	Maintenance Domain: MD0_LEVEL0, MD-name: MD0_LEVEL0, Type: string, Level: 0
	Maintenance Association: BD_CFM2001_PE-to-CE, MA-name: BD_CFM2001_PE-to-CE, Type: string

	Defects: X - DefXconCCM, E - DefErrorCCM, L - DefRemoteCCM, M - DefMACstatus, R - DefRDICCM

	Local MEPs:
	  +--------+-----------------+-------------------+-----------+-------------+--------------+
	  | MEP-ID | Interface       | MAC Address       | Direction | Admin State | CCM TX State |
	  +========+=================+===================+===========+=============+==============+
	  | 1      | bundle-1.2001   | 7c:fe:90:57:73:10 | down      | enabled     | enabled      |
	  +--------+-----------------+-------------------+-----------+-------------+--------------+
	Remote MEPs:
	  +--------+--------------+---------+------------------+-------------+
	  | MEP-ID | CCM RX State | RDI bit | Interface Status | Port Status |
	  +========+==============+=========+==================+=============+
	  | 2      | rmep-ok      | true    | up               | up          |
	  +--------+--------------+---------+------------------+-------------+
	Local MIPs:
	  +--------+-----------------+-------------------+-------------+
	  | MIP    | Interface       | MAC Address       | Admin State |
	  +========+=================+===================+=============+
	  | MyMIP1 | bundle-1.2001   | 7c:fe:90:57:73:10 | disabled    |
	  +--------+-----------------+-------------------+-------------+


	Maintenance Domain: MD4_LEVEL4, MD-name: MD4_LEVEL4, Type: string, Level: 4
	Maintenance Association: BD_CFM2001_PE-to-PE, MA-name: BD_CFM2001_PE-to-PE, Type: string

	Defects: X - DefXconCCM, E - DefErrorCCM, L - DefRemoteCCM, M - DefMACstatus, R - DefRDICCM

	Local MEPs:
	  +--------+---------------+-----------+-------------+--------------+-------------+
	  | MEP-ID | Interface     | Direction | Admin State | CCM TX State | Defects     |
	  +========+===============+===========+=============+==============+=============+
	  | 38     | bundle-1.2001 | up        | enabled     | enabled      | L           |
	  +--------+---------------+-----------+-------------+--------------+-------------+
	Remote MEPs:
	  +--------+--------------+---------+-------------------------+--------------------+
	  | MEP-ID | CCM RX State | RDI bit | Interface Status        | Port Status        |
	  +========+==============+=========+=========================+====================+
	  | 11     | rmep-failed  | false   | no-interface-status-tlv | not-port-state-tlv |
	  +--------+--------------+---------+-------------------------+--------------------+
	Local MIPs:
	  N/A

.. **Help line:** Display CFM information per interface

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| TBD     | Command introduced        |
+---------+---------------------------+