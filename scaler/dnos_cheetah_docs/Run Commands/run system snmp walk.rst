run system snmp walk
--------------------

**Minimum user role:** viewer

To retrieve and display the SNMP object values that are associated with the requested object identifier (oid):

**Command syntax: run system snmp walk {[oid] \| [mib-name]}** {full \| numerical} log [log-file-name]

**Command mode:** operation 

**Note**

- This command is executed using a specific community (v2) named dn_community, which has a "view" configuration attached, named view_default. The output will be displayed within the scope of the supported configured view for the community. This view is restricted only from inside the system (local host). No Lawful Interception (LI) MIBs are exported.

.. - Restricted view response:

	- No LI mibs are exported

	- Linux implementation examples:

	- For SNMP v2c configuration:

	- snmpwalk -v 2c -c dn_community <local-host address> <mib-oid/name>

	- for logging: snmpwalk -v 2c -c dn_community <local-host address> <mib-oid/name> -Lf <log-file>

**Parameter table**

The parameters are:

+---------------+------------------------------------------------------------------------------------------------+
| Parameter     | Description                                                                                    |
+===============+================================================================================================+
| OID           | Reference the command using a specific object identifier.                                      |
+---------------+------------------------------------------------------------------------------------------------+
| MIB name      | Reference the command using a specific object MIB name                                         |
+---------------+------------------------------------------------------------------------------------------------+
| Full          | Include the full list of MIB objects when displaying an OID                                    |
+---------------+------------------------------------------------------------------------------------------------+
| Numerical     | Controls whether you want to display enumerated lists numerically or with textual translations |
+---------------+------------------------------------------------------------------------------------------------+
| Log file name | Give a meaningful name to the log file                                                         |
|               | Minimum user role:                                                                             |
|               |                                                                                                |
|               | Operator                                                                                       |
+---------------+------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# run system snmp walk  1.3.6.1.2.1.1
	SNMPv2-MIB::sysDescr.0 = STRING: DRIVENETS LTD. Virtual Router, DNOS [5.1.1.97], Copyright 2017 DRIVENETS LTD.
	SNMPv2-MIB::sysObjectID.0 = OID: SNMPv2-SMI::enterprises.49739
	DISMAN-EVENT-MIB::sysUpTimeInstance = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysContact.0 = STRING: support@drivenets.com
	SNMPv2-MIB::sysName.0 = STRING: dnRouter
	SNMPv2-MIB::sysLocation.0 = STRING: Undefined
	SNMPv2-MIB::sysORLastChange.0 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORID.1 = OID: SNMP-MPD-MIB::snmpMPDCompliance
	SNMPv2-MIB::sysORID.2 = OID: SNMP-USER-BASED-SM-MIB::usmMIBCompliance
	SNMPv2-MIB::sysORID.3 = OID: SNMP-FRAMEWORK-MIB::snmpFrameworkMIBCompliance
	SNMPv2-MIB::sysORID.4 = OID: SNMP-VIEW-BASED-ACM-MIB::vacmBasicGroup
	SNMPv2-MIB::sysORID.5 = OID: TCP-MIB::tcpMIB
	SNMPv2-MIB::sysORID.6 = OID: UDP-MIB::udpMIB
	SNMPv2-MIB::sysORID.7 = OID: SNMP-NOTIFICATION-MIB::snmpNotifyFullCompliance
	SNMPv2-MIB::sysORID.8 = OID: NOTIFICATION-LOG-MIB::notificationLogMIB
	SNMPv2-MIB::sysORDescr.1 = STRING: The MIB for Message Processing and Dispatching.
	SNMPv2-MIB::sysORDescr.2 = STRING: The management information definitions for the SNMP User-based Security Model.
	SNMPv2-MIB::sysORDescr.3 = STRING: The SNMP Management Architecture MIB.
	SNMPv2-MIB::sysORDescr.4 = STRING: View-based Access Control Model for SNMP.
	SNMPv2-MIB::sysORDescr.5 = STRING: The MIB module for managing TCP implementations
	SNMPv2-MIB::sysORDescr.6 = STRING: The MIB module for managing UDP implementations
	SNMPv2-MIB::sysORDescr.7 = STRING: The MIB modules for managing SNMP Notification, plus filtering.
	SNMPv2-MIB::sysORDescr.8 = STRING: The MIB module for logging SNMP Notifications.
	SNMPv2-MIB::sysORUpTime.1 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.2 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.3 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.4 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.5 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.6 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.7 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.8 = Timeticks: (0) 0:00:00.00
	
	dnRouter# run system snmp walk SNMPv2-MIB
	SNMPv2-MIB::sysDescr.0 = STRING: DRIVENETS LTD. Virtual Router, DNOS [5.1.1.97], Copyright 2017 DRIVENETS LTD.
	SNMPv2-MIB::sysObjectID.0 = OID: SNMPv2-SMI::enterprises.49739
	DISMAN-EVENT-MIB::sysUpTimeInstance = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysContact.0 = STRING: support@drivenets.com
	SNMPv2-MIB::sysName.0 = STRING: dnRouter
	SNMPv2-MIB::sysLocation.0 = STRING: Undefined
	SNMPv2-MIB::sysORLastChange.0 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORID.1 = OID: SNMP-MPD-MIB::snmpMPDCompliance
	SNMPv2-MIB::sysORID.2 = OID: SNMP-USER-BASED-SM-MIB::usmMIBCompliance
	SNMPv2-MIB::sysORID.3 = OID: SNMP-FRAMEWORK-MIB::snmpFrameworkMIBCompliance
	SNMPv2-MIB::sysORID.4 = OID: SNMP-VIEW-BASED-ACM-MIB::vacmBasicGroup
	SNMPv2-MIB::sysORID.5 = OID: TCP-MIB::tcpMIB
	SNMPv2-MIB::sysORID.6 = OID: UDP-MIB::udpMIB
	SNMPv2-MIB::sysORID.7 = OID: SNMP-NOTIFICATION-MIB::snmpNotifyFullCompliance
	SNMPv2-MIB::sysORID.8 = OID: NOTIFICATION-LOG-MIB::notificationLogMIB
	SNMPv2-MIB::sysORDescr.1 = STRING: The MIB for Message Processing and Dispatching.
	SNMPv2-MIB::sysORDescr.2 = STRING: The management information definitions for the SNMP User-based Security Model.
	SNMPv2-MIB::sysORDescr.3 = STRING: The SNMP Management Architecture MIB.
	SNMPv2-MIB::sysORDescr.4 = STRING: View-based Access Control Model for SNMP.
	SNMPv2-MIB::sysORDescr.5 = STRING: The MIB module for managing TCP implementations
	SNMPv2-MIB::sysORDescr.6 = STRING: The MIB module for managing UDP implementations
	SNMPv2-MIB::sysORDescr.7 = STRING: The MIB modules for managing SNMP Notification, plus filtering.
	SNMPv2-MIB::sysORDescr.8 = STRING: The MIB module for logging SNMP Notifications.
	SNMPv2-MIB::sysORUpTime.1 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.2 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.3 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.4 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.5 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.6 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.7 = Timeticks: (0) 0:00:00.00
	SNMPv2-MIB::sysORUpTime.8 = Timeticks: (0) 0:00:00.00
	

.. **Help line:** run snmp walk over mib name or oid

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 5.1.0   | Command introduced |
+---------+--------------------+


