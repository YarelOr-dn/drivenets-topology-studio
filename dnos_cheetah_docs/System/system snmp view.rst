system snmp view
----------------

**Minimum user role:** operator

A view is a collection of MIB object types that you want to group together to restrict or provide access to SNMP objects. The system has a single default view named "viewdefault". This view includes all MIBs in the system (i.e. no exclusions). You can configure 10 different views with 10 different OIDs.

To configure an SNMP View:

**Command syntax: mib {[oid \| mib-name]} {include \| exclude}**

**Command mode:** config

**Hierarchies**

- system snmp

**Note**

- Notice the change in prompt.

.. - view can contain multiple include/exclude mibs/oid

	- By default, the system holds a single view named "viewdefault". this view includes all mibs in the system

	- Per view, Matching include/exclude is done using longest-prefix-match while exclude > include

	- (excluded oids have prioirty vs included oids).

	- For example:

	- INCLUDE: 1.3.6.1.2.1.2.2.1.2 (ifDescr)

	- EXCLUDE: 1.3.6.1.2.1.2 (ifTable)

	- The results of doing a walk on ifTable will produce only ifDescr.

	- If the same OID is both included and excluded, then it is excluded.

	- no command removes the snmp view configuration, or the specific mib configuration

	- There should be 3 OIDs that should be excluded by default:

	- 1.3.6.1.6.3.15 (snmpUsmMIB)

	- 1.3.6.1.6.3.16 (snmpVacmMIB)

	- 1.3.6.1.6.3.18 (snmpCommunityMIB)

	- Rest of the OIDs are included.

**Parameter table**

+-----------+-----------------------------------------+
| Parameter | Description                             |
+===========+=========================================+
| view-name | Provide a name for the view collection. |
+-----------+-----------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# view MyViewName 
	dnRouter(cfg-system-snmp-view)# mib 1.3.6.1.2.1.1 include
	dnRouter(cfg-system-snmp-view)# mib 1.3.6.1.2.1.1.5 exclude
	dnRouter(cfg-system-snmp-view)# mib BGP4-MIB include
	

	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp)# no view MyViewName
	dnRouter(cfg-system-snmp-view)# no mib 1.3.6.1.2.1.1 
	dnRouter(cfg-system-snmp-view)# no mib BGP4-MIB

.. **Help line:** Configure system snmp view

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 5.1.0   | Command introduced                  |
+---------+-------------------------------------+
| 6.0     | Applied new hierarchy for SNMP      |
+---------+-------------------------------------+
| 9.0     | Applied new hierarchy for SNMP view |
+---------+-------------------------------------+


