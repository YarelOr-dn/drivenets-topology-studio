show dnos-internal ncp system info
----------------------------------

**Minimum user role:** viewer

To displays information on the system from the perspective of the NCP:

**Command syntax:show dnos-internal ncp [ncp-id] system info**

**Command mode:** operation

**Parameter table**

+---------------+-------------------------------------------------------+----------------------------+
|               |                                                       |                            |
| Parameter     | Description                                           | Range                      |
+===============+=======================================================+============================+
|               |                                                       |                            |
| ncp-id        | Display the information for the specified NCP only    | 0..cluster type maximum -1 |
|               |                                                       |                            |
|               |                                                       | \* all NCPs                |
+---------------+-------------------------------------------------------+----------------------------+

**Example**
::

	dnRouter#  show dnos-internal ncp * system info

	NCP 0 Table: /system_info/show
	system_id:               84:40:76:72:80:72
	system_name:             dnRouter
	system_description:      DRIVENETS Network Cloud Router
	mgmt_ifname:
	dnos_version:            11.5.1.0
	version:                 1
	master_ncp_id:           0
	initial_uptime_set:      1
	initial_uptime:          18002
	initial_monotonic_time:  540378173
	cur_uptime:              364576

.. **Help line:** Displays DNOS internal information on the system from NCP perspective

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.5        | Command introduced    |
+-------------+-----------------------+
