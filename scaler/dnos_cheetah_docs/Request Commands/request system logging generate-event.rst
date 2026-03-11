request system logging generate-event 
-------------------------------------

**Minimum user role:** operator

You can request the system to generate system events, for example for testing purposes. The system will generate a single instance of the requested events. If events are bound to SNMP traps, the system will also send SNMP traps according to the system configuration. However, system configuration, such as SNMP trap suppression or logging events suppression, have priority over the event generation. Therefore, if an event or trap is suppressed according to the configuration, it won't be sent even if it was generated successfully using the request command.

You can view the required event-attributes by typing "?" after the event-name. When specifying multiple event-attributes, the help command ("?") only shows the remaining available attributes.

To set the system to generate system events:


**Command syntax: request system logging generate-event group [event-group] event [event-name]** event-attribute [event-attribute]

**Command mode:** operational

**Note**

- You must specified all the required attributes defined in the system event for the event to be generated. There are no default values per generated event.

* System configurations such as snmp trap suppression or logging events suppression have priority over the event generation. This means that if an event or trap is suppressed by configuration, it won't be sent **even if it was generated successfully by this command**.


..
	**Internal Note**

	- System shall generate auto-complete attributes (for the user to fill) according the output in "show system logging system-events group".

	- System shall validate the types of each attribute (i.e uint32 cannot get string type or negative integer), if validation fails, user will get an error message.

	- System shall **not** perform logical context validation (i.e user can send linkUp event with Admin Status down parameter)


**Parameter table**

+--------------------+------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
|                    |                                                                                                                                    |                                                         |
| Parameter          | Description                                                                                                                        | Range                                                   |
+====================+====================================================================================================================================+=========================================================+
|                    |                                                                                                                                    |                                                         |
| event-group        | The event group                                                                                                                    | See the SNMP Traps and   System Logs Reference Guide    |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
|                    |                                                                                                                                    |                                                         |
| event-name         | The name of the event that you want to generate                                                                                    | Any event in the specified event-group                  |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
|                    |                                                                                                                                    |                                                         |
| event-attribute    | You must specify all the required attributes   defined in the system event. There are no default values for generated   events.    | \-                                                      |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+

**Example**
::

	dnRouter# request system logging generate-event group interfaces event if_link_state_change_up ?

	if_admin_status          An integer value for if_admin_status
	if_index                 An integer value for if_index
	if_name                  A string value for if_name
	if_oper_status           An integer value for if_oper_status
	new_state                A string value for new_state

	dnRouter# request system logging generate-event group interfaces event if_link_state_change_up new_state up if_name bundle-1.800 if_index 123 ?

	if_admin_status          An integer value for if_admin_status
	if_oper_status           An integer value for if_oper_status

	dnRouter# request system logging generate-event group interfaces event if_link_state_change_up new_state up if_name bundle-1.800 if_index 123 if_admin_status 1 if_oper_status 1

	system event if_link_state_change_up was generated successfully
	snmp trap linkUp was generated successfully

	dnRouter# request system logging generate-event group interfaces event if_link_state_change_up new_state up if_name spoofed-interface if_index 123 if_admin_status 1 if_oper_status 1

	system event if_link_state_change_up was generated successfully
	snmp trap linkUp was generated successfully

	dnRouter# request system logging generate-event group interfaces event if_link_state_change_up new_state up 

	Error: Incomplete command

	dnRouter# request system logging generate-event group interfaces event if_link_state_change_up new_state up if_name spoofed-interface if_index abc if_admin_status 1 if_oper_status 1

	Error: Invalid argument for if_index

	dnRouter# request system logging generate-event group system event ncp_state_change ?

	ncp_id             An integer value for ncp_id
	new_state          A string value for new_state
	old_state          A string value for old_state

	dnRouter# request system logging generate-event group system event ncp_state_change old_state down new_state up ncp_id 3000

	system event ncp_state_change was generated successfully
	snmp trap entConfigChange was generated successfully

	dnRouter# request system logging generate-event group system event ncp_state_change old_state down new_state A ncp_id 3000

	system event ncp_state_change was generated successfully
	snmp trap entConfigChange was generated successfully

	dnRouter# request system logging generate-event group system event system_cold_start

	system event system_cold_start was generated successfully
	snmp trap coldStart was generated successfully

	dnRouter# request system logging generate-event group isis event isis_neighbor_adjacency_up ?

	if_index                    An integer value for if_index
	if_name                     A string value for if_name
	instance                    A string value for instance
	level                       An enumeration for level
	link_state_pdu_id           A binary value for link_state_pdu_id
	neighbor_system_id          A string value for neighbor_system_id
	state                       An enumeration for state

	dnRouter# request system logging generate-event group isis event isis_neighbor_adjacency_up instance foo neighbor_system_id foo if_name foo if_index 123 level 1 link_state_pdu_id 0 state 3

	system event isis_neighbor_adjacency_up was generated successfully
	snmp trap isisAdjacencyChange was generated successfully

.. **Help line:** request system to generate system events

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 12.0        | Command introduced    |
+-------------+-----------------------+