show services sla-probe results brief - N/A for this version
------------------------------------------------------------

**Command syntax: show services sla-probe results brief** owner [owner] test [test]

**Description:** display sla-probe results of last test cycle

**CLI example:**
::

	dnRouter# show services sla-probe results brief

	| Owner     | Test      | Target    | Status           | Timestamp               | RTT(avg)  |
	|-----------+-----------+-----------+------------------+-------------------------+-----------|
	| MyOwner1  | MyTest1   | 1.1.1.1   | responseReceived | Thu Feb 9 07:22:39 2017 | 191.13 ms |
	| MyOwner2  | MyTest1   | 1.2.3.4   | requestTimedOut  | Thu Feb 9 07:22:39 2017 |           |
	| MyOwner2  | MyTest2   | 15.12.1.3 | requestTimedOut  | Thu Feb 9 07:22:39 2017 |           |

	dnRouter# show services sla-probe results brief owner MyOwner2

	| Owner     | Test      | Target    | Status           | Timestamp               | RTT(avg)  |
	|-----------+-----------+-----------+------------------+-------------------------+-----------|
	| MyOwner2  | MyTest1   | 1.2.3.4   | requestTimedOut  | Thu Feb 9 07:22:39 2017 |           |
	| MyOwner2  | MyTest2   | 15.12.1.3 | requestTimedOut  | Thu Feb 9 07:22:39 2017 |           |


	dnRouter# show services sla-probe results brief owner MyOwner2 test MyTest2

	| Owner     | Test      | Target    | Status           | Timestamp               | RTT(avg)  |
	|-----------+-----------+-----------+------------------+-------------------------+-----------|
	| MyOwner2  | MyTest2   | 15.12.1.3 | requestTimedOut  | Thu Feb 9 07:22:39 2017 |           |

**Command mode:** operational

**TACACS role:** viewer

**Note:** Instead of "destination unreachable" status, "requestTimedOut" will be shown.

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
| Status         | responseReceived, unknown, internalError, requestTimedOut, noRouteToTarget, invalidHostAddress |               |
+----------------+------------------------------------------------------------------------------------------------+---------------+
| Timestamp      | Day Mon D HH:MM:SS YYYY                                                                        |               |
+----------------+------------------------------------------------------------------------------------------------+---------------+
| RTT(avg)       | Average Round Trip Time in ms                                                                  |               |
+----------------+------------------------------------------------------------------------------------------------+---------------+

+------------+---------------------------------------+----------------------------+
| Protocol   | String                                | IP protocol                |
+============+=======================================+============================+
| Src-Port   | 1-65535                               | L4 source port             |
+------------+---------------------------------------+----------------------------+
| Dst-Port   | 1-65535                               | L4 destination port        |
+------------+---------------------------------------+----------------------------+
| Ingress-IF | ge<interface speed>-<A>/<B>/<C>       | Ingress interface per flow |
|            |                                       |                            |
|            | geX-<f>/<n>/<p>.<sub-interface id>    |                            |
|            |                                       |                            |
|            | bundle-<bundle-id>                    |                            |
|            |                                       |                            |
|            | bundle-<bundle-id>.<sub-interface-id> |                            |
+------------+---------------------------------------+----------------------------+
| Packet     | 32 bits counter                       |                            |
+------------+---------------------------------------+----------------------------+
| Octets     | 32 bits counter                       |                            |
+------------+---------------------------------------+----------------------------+
| TCP flags  | Flag map:                             | U: Urgent                  |
|            |                                       |                            |
|            | UAPRSF                                | A: Ack                     |
|            |                                       |                            |
|            |                                       | P: Push                    |
|            |                                       |                            |
|            |                                       | R: Reset                   |
|            |                                       |                            |
|            |                                       | S: Syn                     |
|            |                                       |                            |
|            |                                       | F: Fin                     |
+------------+---------------------------------------+----------------------------+
