clear nat counters
----------------------

**Minimum user role:** operator

To clear counters per specific NAT instance

**Command syntax: clear nat counters** [instance-name]

**Command mode:** operation

.. **Hierarchies**

**Parameter table:**

+---------------+-----------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+-------------+
|               |                                                                                                                 |                                                                   |             |
| Parameter     | Description                                                                                                     | Range                                                             | Default     |
+===============+=================================================================================================================+===================================================================+=============+
|               |                                                                                                                 | Any configured nat instance                                       |             |
| instance-name | Enter name of the specific NAT instance                                                                         |                                                                   | \-          |
+---------------+-----------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+-------------+

**Note**

The following counters presented by “show network-services nat counters” refer to the interface counters and not to NAT instance counters:
Outbound statistics
- Total frames RX (rate)
- Total L3 dropped packets
- Total frames TX (rate)
Inbound statistics
- Total frames RX (rate)
- Total L3 dropped packets
- Total frames TX (rate)

The above counters are presented as part “show network-services nat counters” output for for operational simplicity sake. The above counters are not cleared by triggering “clear nat counters” command. To clear the above counters, user must use “clear interface counters” command

**Example**
::

	dnRouter# clear nat counters CUSTOMER_1
	Counters where cleared for NAT instance CUSTOMER_1


.. **Help line:** Clear counters per specific NAT instance

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 18.2        | Command introduced    |
+-------------+-----------------------+