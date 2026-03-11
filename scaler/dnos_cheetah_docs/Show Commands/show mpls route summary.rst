show mpls route summary
-----------------------

**Minimum user role:** viewer

The show mpls route summary command displays the number of RIB routes and FIB entries stored in the MPLS routing table.



**Command syntax: show mpls route summary**

**Command mode:** operational


**Example**
::

	dnRouter# show mpls route summary

	| Route Source | Routes  (vrf default) |
	+--------------+-----------------------+
	| bgp          | 309                   |
	| isis-sr      | 8317                  |
	| ospf-sr      | 0                     |
	| ldp          | 244                   |
	| mldp         | 0                     |
	| rsvp         | 8                     |
	| Totals       | 8878                  |


.. **Help line:** show mpls route table summary

**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 5.1.0   | Command introduced     |
+---------+------------------------+
| 9.0     | Updated command output |
+---------+------------------------+
| 17.1    | Added support for mLDP |
+---------+------------------------+
