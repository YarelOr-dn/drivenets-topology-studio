show system logging system-events group
---------------------------------------

**Minimum user role:** viewer

Displays information on the specific event or for all events belonging to the specific event-group, per specific event.



**Command syntax: show system logging system-events group [event-group] event [event-name]** 

**Command mode:** operational



.. 
	**Internal Note**

	- this output required for understanding the required attributes in event generation using the command "request system logging generate-event"

	- the output indicates if the event contains snmp trap


**Parameter table**

+-------------+----------------------------------------------+-----------------------------------------------------+---------+
| Parameter   | Description                                  | Range                                               | Default |
+=============+==============================================+=====================================================+=========+
| event-group | The group with which the event is associated | management                                          | \-      |
|             |                                              | system                                              |         |
|             |                                              | interfaces                                          |         |
|             |                                              | lacp                                                |         |
|             |                                              | lldp                                                |         |
|             |                                              | rib-manager                                         |         |
|             |                                              | bgp                                                 |         |
|             |                                              | bfd                                                 |         |
|             |                                              | isis                                                |         |
|             |                                              | rsvp                                                |         |
|             |                                              | ospf                                                |         |
|             |                                              | tcp                                                 |         |
|             |                                              | pcep                                                |         |
|             |                                              | platform                                            |         |
|             |                                              | twamp                                               |         |
|             |                                              | aaa                                                 |         |
|             |                                              | fib-manager                                         |         |
|             |                                              | Multicast                                           |         |
|             |                                              | PIM                                                 |         |
|             |                                              | MSDP                                                |         |
|             |                                              | clock                                               |         |
+-------------+----------------------------------------------+-----------------------------------------------------+---------+
| event-name  | The name of the specific event               | Refer to SNMP Traps and System Logs Reference Guide | \-      |
+-------------+----------------------------------------------+-----------------------------------------------------+---------+

**Example**
::

	dnRouter# show system logging system-events group interfaces event IF_LINK_STATE_CHANGE_DOWN

	IF_LINK_STATE_CHANGE_DOWN
	description: "The link state on the interface has moved to a 'down' state. The link state changed due to a link failure."
	message string: "Interface {if_name} link state has changed to {new_state}"
	snmp trap name: "linkDown"
	snmp trap oid: "1.3.6.1.6.3.1.1.5.3"
	required attributes:

		new_state {
			type string;
			description "Interface state";
		}

		if_name {
			type string;
			description "Interface name";
		}

		if_index {
			type uint32;
			description "SNMP Interface index";
		}

		if_admin_status {
			type uint32;
			description "SNMP Admin Status
	SYNTAX INTEGER up(1), down(2), testing(3)";
		}

		if_oper_status {
			type uint32;
			description "SNMP Oper Status
	SYNTAX INTEGER up(1), down(2), testing(3)";
		}

	dnRouter# show system logging system-events group interfaces event IF_LINK_STATE_CHANGE
	
	IF_LINK_STATE_CHANGE
	description: "The link state on the interface has changed."
	message string: "Interface {if_name} link state changed from {old_state} to {new_state}. Lanes: {active_lane_id_list} are up"
	snmp trap name: "None"
	snmp trap oid: "None"
	required attributes:

		if_name {
			type string;
			description "Interface name";
		}

		new_state {
			type string;
			description "Current interface state";
		}

		old_state {
			type string;
			description "Previous interface State";
		}

		active_lane_id_list {
			type string;
			description "All lane ids which their status is up";
		}

	dnRouter# show system logging system-events group system event NCM_STATE_CHANGE_DISCONNECTED

	NCM_STATE_CHANGE_DISCONNECTED
	description: "The NCM is disconnected."
	message string: "NCM {ncm_id} state has changed from {old_state} to {new_state}"
	snmp trap name: "entConfigChange"
	snmp trap oid: "1.3.6.1.2.1.47.2.0.1"
	required attributes:

		old_state {
			type string;
			description "NCM old state";
		}

		new_state {
			type string;
			description "NCM new state";
		}

		ncm_id {
			type string;
			description "NCM ID";
		}

.. **Help line:** show system logging system-events group

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


