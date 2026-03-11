show system snmp traps
----------------------

**Minimum user role:** viewer

The following command displays a list of the SNMP traps with their current status. You can filter the display by trap-type.

**Command syntax: show system snmp traps** [trap-type]

**Command mode:** operational



..
	**Internal Note**

	- bfd traps supported in v11.1

**Parameter table**

For each trap, the following information is displayed:

+-----------+-------------------------------------------------------------------------+-----------+
| Field     | Description                                                             | Range     |
+===========+=========================================================================+===========+
| Trap type | The group to which the trap belongs                                     | Interface |
|           |                                                                         | System    |
|           |                                                                         | BGP       |
|           |                                                                         | OSPF      |
|           |                                                                         | LDP       |
+-----------+-------------------------------------------------------------------------+-----------+
| Trap name | List of supported trap names                                            | \-        |
+-----------+-------------------------------------------------------------------------+-----------+
| Status    | Displays whether the trap is enabled or disabled (see system snmp trap) | Enabled   |
|           |                                                                         | Disabled  |
+-----------+-------------------------------------------------------------------------+-----------+

**Example**
::

	dnRouter# show system snmp traps 
	
	| Trap type    | Trap name                    | Status     | 
	|--------------|------------------------------|------------|
	| interface    | linkUp                       | enabled    | 
	| interface    | linkDown                     | disabled   | 
	| system       | coldStart                    | enabled    | 
	| bgp          | bgpEstablished               | enabled    | 
	| bgp          | bgpBackwardTransNotification | disabled   | 
	| ospf         | ospfIfStateChange            | enabled    | 
	| ospf         | ospfNbrStateChange           | disabled   | 
	| ldp          | mplsLdpSessionUp             | enabled    | 
	| ldp          | mplsLdpSessionDown           | disabled   |
	| bfd          | dnBfdSessionUp               | enabled    | 
	| bfd          | dnBfdSessionDown             | disabled   | 
	 
	
	
	
	dnRouter# show system snmp traps interface
	
	| Trap type    | Trap name             | Status     | 
	|--------------|-----------------------|------------|
	| interface    | linkUp                | enabled    | 
	| interface    | linkDown              | disabled   | 
	
	dnRouter# show system snmp traps bgp 
	
	| Trap type    | Trap name                    | Status     | 
	|--------------|------------------------------|------------|
	| bgp          | bgpEstablished               | enabled    | 
	| bgp          | bgpBackwardTransNotification | disabled   | 
	

.. **Help line:** show system snmp traps

**Command History**

+---------+---------------------+
| Release | Modification        |
+=========+=====================+
| 5.1.0   | Command introduced  |
+---------+---------------------+
| 6.0     | Added BFD trap type |
+---------+---------------------+
| 9.0     | Removed BFD support |
+---------+---------------------+

