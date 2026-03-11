show services performance-monitoring endpoint-delay sessions
------------------------------------------------------------

**Minimum user role:** viewer

This command displays information on active Simple TWAMP data sessions.

To display the active Simple TWAMP sessions in the system:

**Command syntax: show services performance-monitoring endpoint-delay sessions** [session-name]

**Command mode:** operational

**Example**
::

	dnRouter# show services performance-monitoring endpoint-delay sessions

	Simple TWAMP Sessions:

	| Session     | Admin    | VRF      | Local Address | Remote Address | Session Uptime  |
	|-------------+----------+----------+---------------+----------------+-----------------|
	| test1       | enabled  | default  | 1.2.3.4       | 1.1.1.1        | 1 day, 01:01:05 |
	| test2       | enabled  | default  | 1.2.3.4       | 2.2.2.2        | 1 day, 01:01:05 |
	| ge100-0/0/0 | disabled | default  | 1.2.3.4       | 3.3.3.3        | 1 day, 01:01:05 |

	Total displayed sessions: 3


	dnRouter# show services performance-monitoring endpoint-delay sessions test1

	Sender-Session: Test1
		Admin state: enabled
		Sender address: 1.2.3.4, sender source port: 65101
		Reflector address: 1.1.1.1, reflector destination port: 862
		DSCP: 48 (CS6)
		VRF: default
		Probe-Count: 60
		Probe-Interval: 1sec
		Overall test duration: 60sec
		
		Test results:
		Current test:
			Test start time: Wed Jun 22 15:02:57 2022
			Test expeceted end time: Wed Jun 22 15:03:57 2022
			Test status: On-going
		Previous tests:
			Test1-Jun-22-2022-15:02:56
			Test results:
			Test start time: Wed Jun 22 15:01:55 2022
			Test end time: Wed Jun 22 15:02:55 2022
			Test status: Completed successfully (No thresholds crossed)
			Test size: 
				Probes sent: 60 probes
				Probes received: 60 probes
				Loss Percentage: 0.0000000
			Round trip delay
				Samples: 60
				Minimum: 1633 usec, Maximum: 118698 usec, Average: 13769 usec
			Jitter
				Samples: 30
				Egress jitter: 106 usec, Ingress jitter: 213 usec, Round trip jitter: 318 usec


	dnRouter# show services performance-monitoring endpoint-delay sessions ge100-0/0/0

	Sender-Session: ge100-0/0/0
		Admin state: disabled
		Sender address: 1.2.3.4, sender source port: N/A
		Reflector address: 1.1.1.1, reflector destination port: 862


.. **Help line:** Displays active Simple TWAMP sessions in system

**Command History**

+---------+------------------------------------------+
| Release | Modification                             |
+=========+==========================================+
| 17.2    | Command introduced                       |
+---------+------------------------------------------+
