show lacp interfaces
--------------------

**Minimum user role:** viewer



The show lacp interfaces command displays the LACP interface configuration and operational values.

**Command syntax: show lacp interfaces** [interface-name]

**Command mode:** operational



**Note**

- This command is applicable to physical and bundle interfaces.

.. - In the case of writing "show lacp interfaces", all bundle interfaces will be shown with their members.

**Parameter table**

+----------------+---------------------------------------------------------------+
| Parameter      | Description                                                   |
+================+===============================================================+
| interface-name | Filters the displayed information to the specified interface. |
+----------------+---------------------------------------------------------------+

The following information is displayed:

+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+--------------------+
| Parameter       | Description                                                                                                                                                                                | Range                                  | Default Value      |
+=================+============================================================================================================================================================================================+========================================+====================+
| system-priority | After negotiations with all systems, the system with the highest priority will be selected as the master and all others as partners.                                                       | 0..65535                               | 1                  |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+--------------------+
| system-id       | Formed by combining the LACP system-priority with the system's ID                                                                                                                          | xx:xx:xx:xx:xx:xx (mac-address format) | Assigned by system |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+--------------------+
| mode            | Packets are exchanged between interfaces in the following modes:                                                                                                                           | Active                                 | Active             |
|                 | Active: the interface initiates negotiation with another interface by sending LACP packets (LACPDUs).                                                                                      | Passive                                |                    |
|                 | Passive: the interface responds to LACP packets it receives but does not initiate LACP negotiation.                                                                                        |                                        |                    |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+--------------------+
| period          | The frequency with which to send LACP PDUs to the partner system. Options: short (every 1 second); long (every 30 seconds).                                                                | Short                                  | Long               |
|                 |                                                                                                                                                                                            | Long                                   |                    |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+--------------------+
| port-priority   | Port priority is used to dynamically group ports into bundles. The priority of the port within the bundle determines which ports have precedence in participating in the bundle interface. | 0..65535                               | 32768              |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+--------------------+
| force-up        | Defines whether or not to force the bundle interface to remain in an "up" state when the partner device undergoes a change that may impact the LACP operation.                             | Enabled                                | Disabled           |
|                 |                                                                                                                                                                                            | Disabled                               |                    |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+--------------------+
| key             | An identifier inherited from the bundle-id. This is not configurable.                                                                                                                      | 1..65535                               | \-                 |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+--------------------+
|                 |                                                                                                                                                                                            | Active                                 |                    |
| port-state      | The port status.                                                                                                                                                                           | Standby                                | \-                 |
|                 |                                                                                                                                                                                            | System-down                            |                    |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+--------------------+
| port-id         | Unique identifier for a physical interface. This is not configurable.                                                                                                                      | 1..65535                               | \-                 |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+--------------------+
|                 |                                                                                                                                                                                            | Aggregatable                           |                    |
| protocol-state  | The protocol status flags.                                                                                                                                                                 | Synchronized                           | \-                 |
|                 |                                                                                                                                                                                            | Collecting                             |                    |
|                 |                                                                                                                                                                                            | Distributing                           |                    |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+--------------------+


**Example**
::

	dnRouter# show lacp interfaces
	
	Local:
	Aggregate Interface: bundle-21
	Mode: active, Period: short, Key: 21
	System-priority: 1, System-id: 11:22:33:44:55:66
	Force-up: disabled
	
	Peer:
	Mode: active, Key: 1
	System-priority: 32768, System-id: aa:bb:cc:dd:ee:ff

	Legend: a - aggregatable, s - synchronized, c - collecting, d - distributing
	
	| Interface    | Role       | Port State | Protocol State | Port Priority | Port Id   | Period  | 
	|--------------+------------+------------+----------------|---------------+-----------+---------|
	| ge100-1/1/1  | actor      | active     | ascd           | 32768         | 10        | short   |
	| ge100-1/1/1  | partner    | active     | ascd           | 32768         | 1         | short   |
	| ge100-2/1/1  | actor      | active     | asc            | 32768         | 11        | short   |
	| ge100-2/1/1  | partner    | active     | asc            | 32768         | 2         | long    |
	| ge100-3/1/1  | actor      | standby    | as             | 32768         | 12        | short   |
	| ge100-3/1/1  | partner    | standby    | as             | 32768         | 3         | short   |
	
	Local:
	Aggregate Interface: bundle-22
	Mode: active, Period: short, Key: 22
	System-priority: 1, System-id: 11:22:33:44:55:66
	Force-up: disabled
	
	Peer:
	Mode: active, Key: 1
	System-priority: 32768, System-id: 11:bb:cc:dd:ee:ff

	Legend: a - aggregatable, s - synchronized, c - collecting, d - distributing
	
	| Interface    | Role       | Port State | Protocol State | Port Priority | Port Id   | Period  | 
	|--------------+------------+------------+----------------|---------------+-----------+---------|
	| ge100-1/1/2  | actor      | active     | ascd           | 32768         | 20        | short   |
	| ge100-1/1/2  | partner    | active     | ascd           | 32768         | 10        | short   |
	| ge100-2/1/2  | actor      | active     | asc            | 32768         | 21        | short   |
	| ge100-2/1/2  | partner    | active     | asc            | 32768         | 20        | short   |
	| ge100-3/1/2  | actor      | standby    | as             | 32768         | 22        | short   |
	| ge100-3/1/2  | partner    | standby    | as             | 32768         | 30        | short   |
	
	
	dnRouter# show lacp interfaces bundle-21
	
	Local:
	Aggregate Interface: bundle-21
	Mode: active, Period: short, Key: 21
	System-priority: 1, System-id: 11:22:33:44:55:66
	Force-up: disabled
	
	Peer:
	Mode: active, Key: 1
	System-priority: 32768, System-id: aa:bb:cc:dd:ee:ff
	
	Legend: a - aggregatable, s - synchronized, c - collecting, d - distributing
	
	| Interface    | Role       | Port State | Protocol State | Port Priority | Port Id   | Period  | 
	|--------------+------------+------------+----------------|---------------+-----------+---------|
	| ge100-1/1/1  | actor      | active     | ascd           | 32768         | 10        | short   |
	| ge100-1/1/1  | partner    | active     | ascd           | 32768         | 1         | short   |
	| ge100-2/1/1  | actor      | active     | asc            | 32768         | 11        | short   |
	| ge100-2/1/1  | partner    | active     | asc            | 32768         | 2         | long    |
	| ge100-3/1/1  | actor      | standby    | as             | 32768         | 12        | short   |
	| ge100-3/1/1  | partner    | standby    | as             | 32768         | 3         | short   |
	
	
	
	dnRouter# show lacp interfaces ge100-1/1/1
	
	Aggregate Interface: bundle-21

	Legend: a - aggregatable, s - synchronized, c - collecting, d - distributing

	| Interface    | Role       | Port State | Protocol State | Port Priority | Port Id   | Period  | 
	|--------------+------------+------------+----------------|---------------+-----------+---------|
	| ge100-1/1/1  | actor      | active     | ascd           | 32768         | 10        | short   |
	| ge100-1/1/1  | partner    | active     | ascd           | 32768         | 1         | short   |
	
	

.. **Help line:** show lacp Interfaces state

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 6.0     | Command introduced                               |
+---------+--------------------------------------------------+
| 10.0    | Removed static mode, min/max links and revertive |
+---------+--------------------------------------------------+
| 16.1    | Added protocol status information                |
+---------+--------------------------------------------------+

