show mpls traffic-engineering cspf
----------------------------------

**Minimum user role:** viewer

Displays the expected rsvp tunnel path according to given tunnel attributes.

To display the expected rsvp tunnel path:

**Command syntax: show mpls traffic-engineering cspf destination [destination]** path [path-name] bandwidth [bandwidth] class-type [class-type] hop-limit [hop-limit] cspf-calculation [equal-cost] path-selection [path-selection] igp-instance [protocol] [instance-name] priority-setup [setup-priority] priority-hold [hold-priority] protected-interface [interface-name] node-protection exclude-srlg [mode] admin-groups [exclude-any] [include-any] [include-all]

**Command mode:** operational




**Parameter table**

+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| Parameter      | Description                                                                                                                         | Range                               | Default                                 |
+================+=====================================================================================================================================+=====================================+=========================================+
| destination    | The IP address of the cspf destination                                                                                              | ipv4 address                        | \-                                      |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| path-name      | A configured explicit path policy name                                                                                              | string                              | \-                                      |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| bandwidth      | The requested tunnel bandwidth                                                                                                      | 0..4294967295                       | 0                                       |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| class-type     | The tunnel class-type                                                                                                               | 0..1                                | 0                                       |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| hop-limit      | The maximum number of nodes the lsp can traverse                                                                                    | 2..255                              | 255                                     |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| equal-cost     | Sets the cspf equal-cost resolution mode                                                                                            | least-fill                          | least-fill                              |
|                |                                                                                                                                     | most-fill                           |                                         |
|                |                                                                                                                                     | random                              |                                         |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| path-selection | Sets the metric type used for CSPF calculations                                                                                     | te-metric                           | te-metric                               |
|                |                                                                                                                                     | igp-metric                          |                                         |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| protocol       | The type of protocol                                                                                                                | isis                                | isis                                    |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| instance-name  | Sets the igp protocol and protocol instance that will be used by cspf in the path calculation                                       | a configured igp instance           | igp instance with lowest admin-distance |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| setup-priority | The priority used when signaling an LSP for this tunnel to determine which of the existing tunnels can be preempted                 | 0..7                                | 7                                       |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| hold-priority  | The priority used when signaling an LSP for this tunnel, to determine if it should be preempted by other LSPs                       | 0..7                                | 0                                       |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| exclude-srlg   | The interface name from which all srlg values, required to be excluded (not avoided) in the tunnel path, will be obtained           | a configured mpls-te interface name | not-set. no interface to exclude        |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| exclude-any    | Link is eligible if it doesn't contain any admin-groups associated with the exclude-any constraint                                  | 0x0..0xffffffff                     | 0x0                                     |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| include-any    | Link is eligible if it contains at least one admin-group associated with the include-any constraint                                 | 0x0..0xffffffff                     | 0x0                                     |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+
| include-all    | Link is eligible if it contains all admin-groups associated with the include constraint (can have more admin-groups than specified) | 0x0..0xffffffff                     | 0x0                                     |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------+-----------------------------------------+

**Example**
::

	dnRouter# show mpls traffic-engineering cspf destination 100.19.19.19

	Tunnel attributes:
		destination 100.19.19.19, igp-instance isis Devtest_CORE_C2, bandwidth 0, class-type 0
		priority-setup 7, priority-hold 0, exclude-srlg N/A
		path N/A, hop-limit 255, cspf-calculation least-fill, path-selection te-metric
		admin-groups 0x0 0x0 0x0

	Ero:
	   5.13.50.1        strict
	   5.19.50.0        strict

   IGP metric: 1313, CSPF metric: 1314

   dnRouter# show mpls traffic-engineering cspf destination 100.19.19.19 bandwidth 2294967295

	Tunnel attributes:
		destination 100.19.19.19, igp-instance isis Devtest_CORE_C2, bandwidth 2294967295, class-type 0
		priority-setup 7, priority-hold 0, exclude-srlg N/A
		path N/A, hop-limit 255, cspf-calculation least-fill, path-selection te-metric
		admin-groups 0x0 0x0 0x0

	No route available toward destination


	IGP metric: 1313, CSPF metric: 1314

   dnRouter# show mpls traffic-engineering cspf destination 99.99.99.99

	Tunnel attributes:
		destination 99.99.99.99, igp-instance isis Devtest_CORE_C2, bandwidth 0, class-type 0
		priority-setup 7, priority-hold 0, exclude-srlg N/A
		path N/A, hop-limit 255, cspf-calculation least-fill, path-selection te-metric
		admin-groups 0x0 0x0 0x0

	Destination unreachable

.. **Help line:**

**Command History**

+---------+-----------------------------------------------------------------+
| Release | Modification                                                    |
+=========+=================================================================+
| 13.2    | Command introduced                                              |
+---------+-----------------------------------------------------------------+
| 15.1    | Added support for te-metric and igp-metric path selection types |
+---------+-----------------------------------------------------------------+

