show services performance-monitoring link-delay interfaces
----------------------------------------------------------

**Minimum user role:** viewer

This command displays information on active link delay measurement sessions.

To display the active link delay measurement sessions in the system:

**Command syntax: show services performance-monitoring link-delay interfaces** [interface-name]

**Command mode:** operational

**Example**
::

	dnRouter# show services performance-monitoring link-delay interfaces

	Link Delay Measurement Sessions:

	| Interface       | Mode    | Admin    | Local Address | Remote Address | Min Delay [uSec] | Last advertisement   |
	|-----------------+---------+----------+---------------+----------------+------------------+----------------------|
	| bundle-2        | static  |          | 1.2.3.4       | 1.1.1.1        | 1000             |                      |
	| ge100-0/0/0     | dynamic | enabled  | 10.4.5.5      | 10.4.5.10      | 169              | 24-Dec-2022-20:41:32 |
	| ge100-0/0/0.100 | dynamic | enabled  | 1::1          | 1::2           | 105              | 24-Dec-2022-20:34:00 |


	dnRouter# show services performance-monitoring link-delay interfaces bundle-2

	Interface: ge100-0/0/0
		Link-Delay-Measurement      : Static
		Minimum Delay (uSec)        : 1000


	dnRouter# show services performance-monitoring link-delay interfaces ge100-0/0/0

	Interface: ge100-0/0/0
		Link-Delay-Measurement      : Dynamic
		Admin state                 : enabled
		Local IP Address            : 10.4.5.5
		Remote IP Address           : 10.4.5.10

		Last advertisement:
			Advertised at: 24-Dec-2022-20:41:32
			Advertised reason: Periodic timer, min delay threshold crossed
			Advertised delays (uSec): avg: 169, min: 113, max: 498, variance: 49

		Candidate advertisement:
			Check scheduled at the end of the current probe (roughly every 120 seconds)
			Aggregated delays (uSec): avg: 203, min: 105, max: 1521, variance: 85
			Rolling average (uSec): 192


	dnRouter# show services performance-monitoring link-delay interfaces ge100-0/0/0.100

	Interface: ge100-0/0/0
		Link-Delay-Measurement      : Dynamic
		Admin state                 : enabled
		Local IP Address            : 1::1
		Remote IP Address           : 1::2

		Last advertisement:
			N/A

		Candidate advertisement:
			Check scheduled at the end of the current probe (roughly every 120 seconds)
			Aggregated delays (uSec): avg: 203, min: 105, max: 1521, variance: 85
			Rolling average (uSec): 192


.. **Help line:** Displays active link delay measurement sessions in system

**Command History**

+---------+------------------------------------------+
| Release | Modification                             |
+=========+==========================================+
| 18.0    | Command introduced                       |
+---------+------------------------------------------+
