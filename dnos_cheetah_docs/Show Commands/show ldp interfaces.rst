show ldp interfaces
-------------------

**Minimum user role:** viewer

To display information about interfaces that are configured for label switching:



**Command syntax: show ldp interfaces**

**Command mode:** operational



**Note**

- LDP sync state is either:

	- **completed:**  (1) Session is up. (2) LDP on-session-delay expired (3) IGP Uses normal metric

	- **in-progress:**  (1) Session is up. (2) LDP on-session-delay not expired (3) IGP uses MAX metric

	- **out-of-sync:**  (1) Session is Down (2) IGP uses MAX metric


**Example**
::

	dnRouter# show ldp interfaces
	| AF   | Interface             |  State     |  Uptime           |  Hello Timers       | LDP-IGP Sync     |
	|      |                       |            |                   | Interval / holdtime | status           |
	+======+=======================+============+===================+=====================+==================+
	| ipv4 | bundle-2.1011         | ACTIVE     |  1 days, 01:09:57 |   5/15              | completed        |
	| ipv4 | bundle-2.1012         | ACTIVE     |  0 days, 09:17:07 |   5/15              | in-progress      |
	| ipv4 | bundle-10.10          | ACTIVE     |  1 days, 01:09:57 |   5/15              | out-of-sync      |
	| ipv4 | bundle-20.24          | ACTIVE     |  0 days, 09:17:07 |   5/15              | completed        |


.. **Help line:** Displays information about LDP enabled interfaces

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+

