show dnos-internal oper-data
----------------------------

**Minimum user role:** viewer

To display operational database information for DNOS processes:

**Command syntax: show dnos-internal oper-data [path]**

**Command mode:** operation



**Note**



**Parameter table**

+---------------+-------------------+------------+-------------+
|               |                   |            |             |
| Parameter     | Description       | Values     | Default     |
+===============+===================+============+=============+
| path          | DNOS Yang path    |  \-        | \-          |
+---------------+-------------------+------------+-------------+

**Example**
::

	dev-dnRouter# show dnos-internal oper-data /drivenets-top/interfaces/interface[name='ge100-0/0/1']/oper-items/counters/ethernet-drop-counters

	interface:ge100-0/0/1
	- rx_errors: 0
	  rx_fcs_errors: 0
	  rx_internal_mac_errors: 0
	  rx_symbol_errors: 0
	  rx_too_long: 0
	  rx_too_short: 0
	  tx_errors: 0


.. **Help line:** Displays the contents in the operational DB

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 13.2        | Command introduced    |
+-------------+-----------------------+
| 18.3        | Removed old oper      |
+-------------+-----------------------+