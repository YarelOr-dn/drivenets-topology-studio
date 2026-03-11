show services sla-probe results - N/A for this version
------------------------------------------------------

**Command syntax: show services sla-probe results** owner [owner] test [test]

**Description:** display sla-probe results (last/previous/all)

**CLI example:**
::

	dnRouter# show services sla-probe results
	
	Owner: MyOwner1, Test: MyTest1
	Target address: 1.1.1.1, Probe type: icmp-ping, Total probes: 1
	Last Result:
	Tx Probes: 5, Rx Probes: 4, Loss%: 20
	Status: responseReceived, Timestamp: Thu Feb 9 07:22:39 2017
	Response TTL: 56
	RTT: min/max/avg/mdev (191.13/191.13/191.13/191.13) ms
	Previous Result:
	Tx Probes: 5, Rx Probes: 5, Loss%: 0
	Status: responseReceived, Timestamp: Thu Feb 9 07:22:39 2017
	Response TTL: 56
	RTT: min/max/avg/mdev (191.13/191.13/191.13/191.13) ms
	All Results:
	Tx Probes: 50, Rx Probes: 48, Loss%: 4
	RTT: min/max/avg/mdev (191.13/191.13/191.13/191.13) ms
	
	Owner: MyOwner2, Test: MyTest1
	Target address: 1.2.3.4, Probe type: icmp-ping, Total probes: 10
	Last Result:
	Tx Probes: 10, Rx Probes: 10, Loss%: 0
	Status: responseReceived, Timestamp: Thu Feb 9 07:22:39 2017
	Response TTL: 56
	RTT: min/max/avg/mdev (191.13/191.13/191.13/191.13) ms
	Previous Result:
	Tx Probes: 10, Rx Probes: 1, Loss%: 90
	Status: requestTimedOut, Timestamp: Thu Feb 9 07:22:39 2017
	Response TTL: 56
	RTT: min/max/avg/mdev (191.13/191.13/191.13/191.13) ms
	All Results:
	Tx Probes: 100, Rx Probes: 91, Loss%: 9
	RTT: min/max/avg/mdev (191.13/191.13/191.13/191.13) ms
	
	dnRouter# show services sla-probe results owner MyOwner2
	
	Owner: MyOwner2, Test: MyTest1
	Target address: 1.2.3.4, Probe type: icmp-ping, Total probes: 10
	Last Result:
	Tx Probes: 10, Rx Probes: 10, Loss%: 0
	Status: responseReceived, Timestamp: Thu Feb 9 07:22:39 2017
	Response TTL: 56
	RTT: min/max/avg/mdev (191.13/191.13/191.13/191.13) ms
	Previous Result:
	Tx Probes: 10, Rx Probes: 1, Loss%: 90
	Status: responseReceived, Timestamp: Thu Feb 9 07:22:39 2017
	Response TTL: 56
	RTT: min/max/avg/mdev (191.13/191.13/191.13/191.13) ms
	All Results:
	Tx Probes: 100, Rx Probes: 91, Loss%: 9
	RTT: min/max/avg/mdev (191.13/191.13/191.13/191.13) ms
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

ICMP probing done via "ping -c -<total-probes>" command.

For last/previous results, timestamp, status and response-ttl relates to the latest probe.

For all results, timestamp, status and response-ttl aren't shown.

pingProbeHistoryEntry mib values (oid 1.3.6.1.2.1.80.1.4.1):

1 - HistoryIndex - assigned by system (not shown in the cli)

2 - HistoryResponse - response-ttl value

3 - HistoryStatus - status value

4 - HistoryLastRC - N/A

5 - HistoryTime - timestamp value

Instead of "destination unreachable" status, "requestTimedOut" will be shown.

**Help line:** show sla-probe results

**Parameter table:**

+----------------+------------------------------------------------------------------------------------------------+---------------+
| Parameter      | Values                                                                                         | Default value |
+================+================================================================================================+===============+
| owner-name     | string [32 char]                                                                               |               |
+----------------+------------------------------------------------------------------------------------------------+---------------+
| test-name      | string [32 char]                                                                               |               |
+----------------+------------------------------------------------------------------------------------------------+---------------+
| target address | A.B.C.D                                                                                        |               |
+----------------+------------------------------------------------------------------------------------------------+---------------+
| total-probes   | 1-15                                                                                           | 1             |
+----------------+------------------------------------------------------------------------------------------------+---------------+
| probe-type     | icmp-ping                                                                                      | Icmp-ping     |
+----------------+------------------------------------------------------------------------------------------------+---------------+
| status         | responseReceived, unknown, internalError, requestTimedOut, noRouteToTarget, invalidHostAddress |               |
+----------------+------------------------------------------------------------------------------------------------+---------------+
| timestamp      | Day Mon D HH:MM:SS YYYY                                                                        |               |
+----------------+------------------------------------------------------------------------------------------------+---------------+
| RTT            | Time in ms                                                                                     |               |
+----------------+------------------------------------------------------------------------------------------------+---------------+
| response-ttl   | 0-255                                                                                          |               |
+----------------+------------------------------------------------------------------------------------------------+---------------+
