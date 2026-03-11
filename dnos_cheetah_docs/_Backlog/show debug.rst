show debug
----------

**Command syntax:show debug**

**Description:** display persistent and non-persistent debug parameters

**CLI example:**
::

	dnRouter# show debug

	Persistent debug parameters:
		debug bgp as4 segment
		debug bgp filters
		debug bgp fsm	
		debug ldp rib


	Non-persistent debug parameters:
		set debug isis route-events
		set rsvp packets
	
	Debug files parameters:
		bgp
			Files per process: 5
			Maximum file size: 512MB 
		isis	
			Files per process: 10
			Maximum file size: 100MB 

	
**Command mode:** operational

**TACACS role:** viewer

**Note:** 

**Help line:** display persistent and non-persistent debug parameters