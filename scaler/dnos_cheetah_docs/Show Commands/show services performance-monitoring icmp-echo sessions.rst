show services performance-monitoring icmp-echo sessions
-------------------------------------------------------

**Minimum user role:** viewer

This command displays information on active ICMP echo IP performance measurement sessions.

To display the active ICMP echo monitoring sessions in the system:

**Command syntax: show services performance-monitoring icmp-echo sessions** [session-name]

**Command mode:** operational

**Example**
::

	dnRouter# show services performance-monitoring icmp-echo sessions

	ICMP Echo IP Performance Monitoring Sessions:

	| Session     | Admin    | VRF      | Local Address | Remote Address | Session Uptime  |
	+-------------+----------+----------+---------------+----------------+-----------------+
	| test1       | enabled  | default  | 1.2.3.4       | 1.1.1.1        | 1 day, 01:01:05 |
	| test2       | enabled  | default  | 1.2.3.4       | 2.2.2.2        | 1 day, 01:01:05 |
	| test3       | disabled | default  | 1.2.3.4       | 3.3.3.3        | 1 day, 01:01:05 |

	Total displayed sessions: 3


	dnRouter# show services performance-monitoring icmp-echo sessions test1

	Session: test1
	  Admin state: enabled, Uptime: 1 day, 01:01:05
	  Source address: 1.2.3.4, session identifier: 100
	  Target address: 1.1.1.1, VRF: default
	  DSCP: 48
	  Probe-Count: 60
	  Probe-Interval: 1sec
	  Probe-Size: 1200 bytes, Padding mode: random
	  Overall test duration: 60sec
		
	  Test results:
		Current test:
		  Test start time: Wed Jun 22 15:02:57 2022
		  Test expeceted end time: Wed Jun 22 15:03:57 2022
		Previous tests:
		  test1-Jun-22-2022-15:02:56
		  Test results:
		  Test start time: Wed Jun 22 15:01:55 2022
		  Test end time: Wed Jun 22 15:02:55 2022
		  Test status: Completed successfully (No thresholds crossed)
		  Loss statistics:
		    Probes sent: 60 probes
		    Probes received: 60 probes
		    Probes lost: 0 probes
		    Loss Percentage: 0.0000000%
		    Successive loss occurences: 0
			  Minimum successive loss: 0 probes, Maximum successive loss: 0 probes
		  Round trip delay
		    Samples: 60
		    Minimum: 1633 usec, Maximum: 118698 usec, Average: 13769 usec
		  Round trip jitter
		    Samples: 30
		    Minimum: 318 usec, Maximum: 322 usec, Average: 320 usec


	dnRouter# show services performance-monitoring icmp-echo sessions test3

	Session: test3
	  Admin state: disabled, Uptime: 0 days, 00:00:00
	  Source address: 1.2.3.4, session identifier: 200
	  Target address: 3.3.3.3, VRF: default
	  DSCP: 48
	  Probe-Count: 60
	  Probe-Interval: 1sec
	  Probe-Size: 1200 bytes, Padding mode: random
	  Overall test duration: 60sec


.. **Help line:** Displays active ICMP echo IP performance monitoring sessions in the system

**Command History**

+---------+------------------------------------------+
| Release | Modification                             |
+=========+==========================================+
| TBD     | Command introduced                       |
+---------+------------------------------------------+
