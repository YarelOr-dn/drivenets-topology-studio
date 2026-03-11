show rsvp interfaces
--------------------

**Minimum user role:** viewer

This command is applicable to the following interfaces:

physical interfaces logical interfaces (sub-interfaces) bundle interfaces bundle sub-interfaces

To display information for RSVP interfaces:

**Command syntax: show rsvp interfaces** [interface-name]

**Command mode:** operational



**Parameter table**

+----------------+---------------------------------------------------------------+
| Parameter      | Description                                                   |
+================+===============================================================+
| no filter      | Displays all RSVP enabled interfaces                          |
+----------------+---------------------------------------------------------------+
| interface-name | Filters the information displayed for the specified interface |
+----------------+---------------------------------------------------------------+

**Example**
::

	dnRouter# show rsvp interfaces
	
	Interface  | IPv4-Address    | operational | auto-bypass protection |   
	-----------+-----------------+-------------+------------------------+
	lo0        |  10.10.10.10/32 | up          | disabled               |
	bundle-1   |  1.0.0.10/24    | up          | enabled                |
	bundle-2   |  3.0.0.10/24    | up          | enabled                |
	
	dnRouter# show rsvp interfaces bundle-1
	
	Interface bundle-1 
	 RSVP state: enabled, operational: up
	 Ipv4-address: 1.0.0.10/24, ifindex 151, mtu 1500
	 refresh-reduction 
	  aggregate: enabled
	    reliable: enabled
	 timers
	   refresh-interval: 5 sec, refresh-multiplier:3 
	 protection 
	   bypass-tunnel: bypass1 
	   auto-bypass: enabled
	
	
	


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+

