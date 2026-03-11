show debug console
------------------

**Command syntax: show debug console** [category]

**Description:** Displays debug availability for console

**CLI example:**
::

	dnRouter# show debug console
	
	OSPF debugging status:
	  Events (persistant)
	  ISA (persistant)  
	  NSM 
	  NSSA 
	
	BGP debugging status:
	  Events (persistant)
	  AS4 
	  FSM 
	
	RIB-Manager debugging status:
	  Events 
	  NHT 
	
	
	dnRouter# show debug console rib-manager
	
	RIB-Manager debugging status:
	  Events 
	  NHT 
	
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

**Help line:** Displays debug availability for console

+------------+---------------------------------------+---------------+
| Parameter  | Values                                | Default value |
+============+=======================================+===============+
| category   | According to `debug table <#debug>`__ |               |
+------------+---------------------------------------+---------------+
| parameters | According to `debug table <#debug>`__ |               |
+------------+---------------------------------------+---------------+
