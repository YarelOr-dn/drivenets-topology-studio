show debug terminal 
--------------------

**Command syntax: show debug terminal** [category]

**Description:** Displays debug availability for console

**CLI example:**
::

	dnRouter# show debugging terminal
	
	OSPF debugging status:
	  Events 
	  ISA 
	  NSM 
	  NSSA 
	
	BGP debugging status:
	  General-events non-persistant on
	  AS4 debugging non-persistant on
	  FSM debugging non-persistant on
	
	RIB-Manager debugging status:
	  Events debugging non-persistant on
	  NHT debugging non-persistant on
	
	ARP debugging status: 
	  General events: non-persistant on
	
	
	dnRouter# show debug terminal arp
	
	ARP debugging status: 
	  General events: non-persistant on
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

**Help line:** Displays debug availability for terminal

+------------+---------------------------------------+---------------+
| Parameter  | Values                                | Default value |
+============+=======================================+===============+
| category   | According to `debug table <#debug>`__ |               |
+------------+---------------------------------------+---------------+
| parameters | According to `debug table <#debug>`__ |               |
+------------+---------------------------------------+---------------+
