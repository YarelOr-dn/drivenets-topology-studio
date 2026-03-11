show system snmp statistics
---------------------------

**Minimum user role:** viewer

You can use the following command to display the number of SNMP requests, responses and traps that the SNMP agent received and sent.



**Command syntax: show system snmp statistics**

**Command mode:** operational




**Example**
::

	dnRouter# show system snmp statistics

	GetRequest PDUs received                150
	GetNextRequest PDUs received          24005
	GetBulkRequest PDUs received           2507
	Response PDUs sent                    26662
	SNMPv2-Trap PDUs sent                  1300


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+

