show services ethernet-oam connectivity-fault-management summary
----------------------------------------------------------------

**Minimum user role:** viewer

To display summary information for Connectivity Fault Management ethernet OAM:


**Command syntax: show services ethernet-oam connectivity-fault-management summary**

**Command mode:** operational

..
	**Internal Note**
	
	-

**Example**
::

	dnRouter# show services ethernet-oam connectivity-fault-management summary

	Connectivity Fault Management Ethernet OAM summary:

	CFM Summary:
	  Number of Maintenance Domains             : 9
	  Number of Maintenance Associations        : 26
	  Number of local MEPs                      : 34
	    Operational                             : 34
	      Down MEPs                             : 23
	      Up MEPs                               : 11
	    Disabled (user configuration)           : 0
	    Disabled (internal error)               : 0
	  Number of remote MEPs                     : 1024
	    Operational                             : 924
	      Remote Defect Indication received     : 100
	      No Remote Defect Indication received  : 824
	    Loss of connectivity                    : 100
	  Number of MIPs                            : 0
	  Number of interfaces                      : 26
	  Number of faulty services                 : 0
	  CCM learning database entries             : 0

	CFM Statistics:
	  CFM PDU Statistics:
	    +--------------+-------------+-------------+
	    | CFM PDUs     | Sent        | Received    |
	    +--------------+-------------+-------------+
	    | CCM          | 2345        | 4321        |
	    | LBM          | 0           | 0           |
	    | LBR          | 0           | 0           |
		| LTM          | 0           | 0           |
		| LTR          | 0           | 0           |
	    +--------------+-------------+-------------+
	  CFM Errors:
	    +----------------------------+-------------+
	    | CFM Errors                 | Received    |
	    +----------------------------+-------------+
	    | Unknown CFM PDUs           | 0           |
	    | Wrong MD Level             | 0           |
	    | CCM Wrong Interval         | 0           |
	    | CCM Wrong Remote-MEP       | 0           |
	    | CCM Wrong MAID             | 0           |
		| Unicast MAC Mismatch       | 0           |
	    | RX Passive Side            | 0           |
	    +----------------------------+-------------+


.. **Help line:** Display CFM summary

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| TBD     | Command introduced        |
+---------+---------------------------+
| TBD     | Added additional counters |
+---------+---------------------------+
