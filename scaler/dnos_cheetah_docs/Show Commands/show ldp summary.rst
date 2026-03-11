show ldp summary
----------------

**Minimum user role:** viewer

The show ldp summary command displays information on a variety of LDP information and configuration.


**Command syntax: show ldp summary**

**Command mode:** operational

**Example**
::

	dnRouter# show ldp summary

	Router id: 51.51.51.51
	Active neighbours: 0
	Active adjacencies: 0
	Capabilities:
	  Multipoint:
		  P2MP: enabled
		  MBB: enabled
		    timeout: 30 sec, switchover delay: 30 sec
	  Graceful restart:
		  restart: enabled, helper mode: enabled
		  reconnect timeout: 90 sec, recovery time: 30 sec
	Load split:
	  state: enabled
	  upstream rebalancing time: 300 sec, downstream rebalancing time: 300 sec
	NSR:
	  state: Ready for all types of restart
	  sub-state: No additional info

.. **Help line:** Displays ldp summary information

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 16.2    | Command introduced                    |
+---------+---------------------------------------+
| 17.1    | Added global capabilities information |
+---------+---------------------------------------+
