show msdp summary
-----------------

**Minimum user role:** viewer

You can use this command to display MSDP summary information.



**Command syntax: show msdp summary**

**Command mode:** operational




**Example**
::

	dnRouter# show msdp summary

	MSDP Information:
		Local Originator-RP          : 1.1.1.1
		Locally generated active SAs :  2345
		External Active SAs          : 34552
		Total SA states              : 36897
		Maximum SAs Limit            : 60000
		SAs threshold                : 45000
		Active Peers                 :    46

	MSDP Statistics:
		MSDP TLV Statistics:
			+--------------+-------------+-------------+
			| MSDP TLVs    |   Sent      |  Received   |
			+--------------+-------------+-------------+
			| Keepalives   |     2345    |    4321     |
			| SAs          |    12345    |    2345     |
			+--------------+-------------+-------------+
    	MSDP Errors:
			+--------------+-------------+
			| MSDP Errors  |  Received   |
			+--------------+-------------+
			| Unknown TLVs |      0      |
			| Error TLVs   |      0      |
			+--------------+-------------+


.. **Help line:** Show MSDP Summary

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+


