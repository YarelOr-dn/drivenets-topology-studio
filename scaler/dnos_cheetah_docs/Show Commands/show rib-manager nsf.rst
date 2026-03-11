show rib-manager nsf
--------------------

**Minimum user role:** viewer

The stalepath-time configured for BGP (see bgp graceful-restart) is used both as a stale timer for the graceful-restart helper and as the BGP-to-RIB purge time. When used as the purge timer, 60 seconds are automatically added to the configured stalepath-time.

This command displays the purge timer per protocol in the RIB. When the protocol is restarted, its stale routes are purged from the RIB after this timer expires.

The global NSF purge time is used by the FIB, when it disconnects from the RIB (e.g. upon NCC switchover, or restart of the RIB-manager process). As the FIB only has one global purge timer, the value of the timer is the highest value of all protocols' purge timers. Therefore, it must wait for all the protocols to converge before it can start purging stale routes. When all protocols have reached the "converged" state, the RIB sends a "converged" message to the FIB, triggering the purge. That is, if all the protocols converge fast enough, the FIB purge will begin regardless of the timer.

To display the RIB manager's non-stop forwarding information:

**Command syntax: show rib-manager nsf**

**Command mode:** operational


The NSF states are:

+--------------------+-------------------------------------------------------------------------------------------------+
| NSF State          | Description                                                                                     |
+====================+=================================================================================================+
| not initialized    | A temporary state before the RIB has determined if this is a normal start-up or an NSF start-up |
+--------------------+-------------------------------------------------------------------------------------------------+
| first_boot         | The RIB has started normally for the first time (e.g. system restart), not doing any NSF        |
+--------------------+-------------------------------------------------------------------------------------------------+
| first_boot_process | The routing protocols had converged after first boot; the RIB is now processing all routes      |
+--------------------+-------------------------------------------------------------------------------------------------+
| normal             | The RIB has finished processing all routes after initial boot (e.g. system restart)             |
+--------------------+-------------------------------------------------------------------------------------------------+
| restart delay      | The RIB is started in NSF mode, waiting for all routing protocols to converge                   |
+--------------------+-------------------------------------------------------------------------------------------------+
| restart process    | The routing protocols had converged; the RIB is now processing all routes                       |
+--------------------+-------------------------------------------------------------------------------------------------+
| done               | The RIB has finished its NSF restart                                                            |
+--------------------+-------------------------------------------------------------------------------------------------+


**Example**
::

	dnRouter# show rib-manager nsf


	NSF State: normal
	NSF Purge Time: 420

	NSF Clients:
	  isis:
	     Purge Time : 180
	     Converged  : Yes

	  rsvp:
	     Purge Time : 90
	     Converged  : Yes

	  ospf:
	     Purge Time : 180
	     Converged  : Yes

	  ospfv3:
	     Purge Time : 180
	     Converged  : Yes

	  ospfv3:
	     Purge Time : 180
	     Converged  : Yes

	  ldp:
	     Purge Time : 240
	     Converged  : Yes

	  bgp:
	     Purge Time : 420
	     Converged  : Yes

.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+


