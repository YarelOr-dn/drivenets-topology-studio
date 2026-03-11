show lacp counters
------------------

**Minimum user role:** viewer

The show lacp counters command displays the LACP counters on either a specific interface or all interfaces.



**Command syntax: show lacp counters** [interface-name]

**Command mode:** operational


..
	**Internal Note**

	- interface-name]: option to specify an interface.


**Parameter table**

+---------------+----------------------------------------------------------+-------------+---------------+
| Parameter     | Description                                              | Range       | Default Value |
+===============+==========================================================+=============+===============+
|               |                                                          | Active      |               |
| Port State    | The port status.                                         | Standby     | \-            |
|               |                                                          | System-down |               |
+---------------+----------------------------------------------------------+-------------+---------------+
| LACPDU rx     | Received Link Aggregation Control Protocol Data Units    | 0..2^64-1   | 0             |
+---------------+----------------------------------------------------------+-------------+---------------+
| LACPDU tx     | Transmitted Link Aggregation Control Protocol Data Units | 0..2^64-1   | 0             |
+---------------+----------------------------------------------------------+-------------+---------------+
| Marker PDU rx | Received Marker Protocol Data Units                      | 0..2^64-1   | 0             |
+---------------+----------------------------------------------------------+-------------+---------------+
| Marker PDU tx | Transmitted Marker Protocol Data Units                   | 0..2^64-1   | 0             |
+---------------+----------------------------------------------------------+-------------+---------------+
| Errors        | Total packet errors per interface                        | 0..2^64-1   | 0             |
+---------------+----------------------------------------------------------+-------------+---------------+
| Last Cleared  | When the counters for the interface were cleared.        | Time format | \-            |
|               |                                                          | Never       |               |
+---------------+----------------------------------------------------------+-------------+---------------+

**Example**
::

	dnRouter# show lacp counters
	
	Aggregate Interface: bundle-21
	| Interface    | Port State | LACPDU rx | LACPDU tx | Marker PDU rx | Marker PDU rx | Errors | Last Cleared      |
	|              |            | [pkts]    | [pkts]    | [pkts]        | [pkts]        | [pkts] |                   |                    
	|--------------+------------+-----------+-----------+---------------+---------------+--------+-------------------|
	| ge100-1/1/1  | active     | 12        | 13         | 10           | 11            | 0      | never             |
	| ge100-2/1/1  | active     | 12        | 13         | 10           | 11            | 0      | 2 days, 12:34:56  |
	| ge100-3/1/1  | standby    | 12        | 13         | 10           | 11            | 0      | never             |
	     
	Aggregate Interface: bundle-22
	| Interface    | Port State | LACPDU rx | LACPDU tx | Marker PDU rx | Marker PDU rx | Errors | Last Cleared      |
	|              |            | [pkts]    | [pkts]    | [pkts]        | [pkts]        | [pkts] |                   |                    
	|--------------+------------+-----------+-----------+---------------+---------------+--------+-------------------|
	| ge100-1/1/2  | active     | 12        | 13         | 10           | 11            | 0      | never             |
	| ge100-2/1/2  | active     | 12        | 13         | 10           | 11            | 0      | 2 days, 12:34:56  |
	| ge100-3/1/2  | standby    | 12        | 13         | 10           | 11            | 0      | never             |
	
	dnRouter# show lacp counters bundle-21
	
	Aggregate Interface: bundle-21
	| Interface    | Port State | LACPDU rx | LACPDU tx | Marker PDU rx | Marker PDU rx | Errors | Last Cleared      |
	|              |            | [pkts]    | [pkts]    | [pkts]        | [pkts]        | [pkts] |                   |                    
	|--------------+------------+-----------+-----------+---------------+---------------+--------+-------------------|
	| ge100-1/1/1  | active     | 12        | 13         | 10           | 11            | 0      | never             |
	| ge100-2/1/1  | active     | 12        | 13         | 10           | 11            | 0      | 2 days, 12:34:56  |
	| ge100-3/1/1  | standby    | 12        | 13         | 10           | 11            | 0      | never             |
	
	dnRouter# show lacp counters ge100-1/1/1
	
	Aggregate Interface: bundle-21
	| Interface    | Port State | LACPDU rx | LACPDU tx | Marker PDU rx | Marker PDU rx | Errors | Last Cleared      |
	|              |            | [pkts]    | [pkts]    | [pkts]        | [pkts]        | [pkts] |                   |                    
	|--------------+------------+-----------+-----------+---------------+---------------+--------+-------------------|
	| ge100-1/1/1  | active     | 12        | 13         | 10           | 11            | 0      | never             |
	
	

.. **Help line:** show lacp counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
