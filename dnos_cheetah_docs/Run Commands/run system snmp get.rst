run system snmp get
-------------------

**Minimum user role:** viewer

To retrieve and display one or more SNMP object values:

**Command syntax: run system snmp get {[oid] \| [mib-name]}** {[oid] \| [mib-name]}.. {full \| numerical} log [log-file-name]

**Command mode:** operation 

**Note**

- This command is executed using a specific community (v2) named dn_community, which has a "view" configuration attached, named view_default. The output will be displayed within the scope of the supported configured view for the community. This view is restricted only from inside the system (local host). No Lawful Interception (LI) MIBs are exported.

.. - Restricted view response:

	- No LI mibs are exported

	- Linux implementation examples:

	- For SNMP v2c configuration:

	- snmpget -v 2c -c dn_community <local-host address> <mib-oid/name>

	- for logging: snmpget -v 2c -c dn_community <local-host address> <mib-oid/name> -Lf <log-file>

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

	dnRouter# run system snmp get sysDescr.0
	SNMPv2-MIB::sysDescr.0 = STRING: DRIVENETS LTD. Virtual Router, DNOS [5.1.1.97], Copyright 2017 DRIVENETS LTD.
	
	dnRouter# run system snmp get sysDescr.0 sysName.0
	SNMPv2-MIB::sysDescr.0 = STRING: DRIVENETS LTD. Virtual Router, DNOS [5.1.1.97], Copyright 2017 DRIVENETS LTD.
	SNMPv2-MIB::sysName.0 = STRING: dnRouter	
	

.. **Help line:** run snmp get over mib name or oid

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 5.1.0   | Command introduced |
+---------+--------------------+


