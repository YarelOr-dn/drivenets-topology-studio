show system uptime
------------------

**Minimum user role:** viewer

To display information on the amount of time that the system is running:



**Command syntax: show system uptime**

**Command mode:** operational



**Note**

- The system uptime reflects the uptime of the active NCC. The uptime counter begins when the last process in the NCC container is in up state.

..	- System uptime is alias to main controller uptime. 

	- Switchover counter reset its values on system reset operation.

	- System uptime start counting once the last process in the NCC containers in up state

	- After showing current time, the configured time-zone will be shown.


**Parameter table**

+--------------+-----------------------------------------------------------+---------------------+---------+
| Parameter    | Description                                               | Range               | Default |
+==============+===========================================================+=====================+=========+
| Current time | Displays the current local time                           | dd-mm-yyyy hh:mm:ss | \-      |
+--------------+-----------------------------------------------------------+---------------------+---------+
| Uptime       | The time lapsed since the NCC containers entered Up state | ddd days, hh:mm:ss  | \-      |
+--------------+-----------------------------------------------------------+---------------------+---------+

**Example**
::

	dnRouter# show system uptime
	System Name: dnRouter
	Current Time: 03-Mar-2020 17:58:48 UTC
	System Start Time: 03-Mar-2020 17:56:48 UTC
	System Uptime: 0 days, 00:02:00
	System Boot Uptime: 0 days, 00:02:35

.. **Help line:** show system uptime

**Command History**

+---------+---------------------------------+
| Release | Modification                    |
+=========+=================================+
| 5.1.0   | Command introduced              |
+---------+---------------------------------+
| 10.0    | Updated to new NCR architecture |
+---------+---------------------------------+
| 11.6    | Updated to show uptime output   |
+---------+---------------------------------+


