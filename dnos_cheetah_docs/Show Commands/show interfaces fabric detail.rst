show interfaces fabric detail
-----------------------------

**Minimum user role:** viewer

To display details on fabric interfaces:


**Command syntax:show interfaces fabric detail**

**Command mode:** operational



**Note**

- If the node is not yet configured or is not connected to the NCC, the state of its fabric interfaces will display "not-exist".

- The operational state relates to the link-state. The uptime for fabric interfaces is with a "watch" interval of 5 seconds and is displayed for interfaces with an operational state "up", otherwise the uptime is "0".

- The syntax for lane ID is: sfiX/Y, where X=the unit ID; Y=the lane port ID.

- The T flag is displayed if the value ≠ 63.


**Example**
::

	dnRouter# show interfaces fabric detail
	
	Interface fab-ncf400-0/0/0
	  SNMP ifindex: 1234
	  Admin state: enabled, Operational state: up, Uptime: 0 days, 00:01:30
	  State transitions: 4, Last cleared: 0 days, 00:00:01
	  Speed: 400Gbps
	  Total Lanes: 8
	  Active Lanes: 7

	  Flags: C - Non-zero CRC rate, S - Non-zero size error-count, G - Non-zero code group error-count
	         M - Link down, misalignment error, L - Link down, SerDes signal lock error
	         R - Link up, but not accepting reachability cells
	         T - Bad link connectivity or link down, based on reachability cells
	
	  | Lane  id      | Operational | Flags   |
	  |---------------+-------------+---------|
	  | 0 (sfi7/0)    | up          | CT      |
	  | 1 (sfi7/1)    | up          |         |
	  | 2 (sfi7/2)    | up          |         |
	  | 3 (sfi7/3)    | up          |         |
	  | 4 (sfi7/4)    | up          |         |
	  | 5 (sfi7/5)    | up          |         |
	  | 6 (sfi7/6)    | up          | R       |
	  | 7 (sfi7/7)    | down        | MT      |
	
	Interface fab-ncp400-0/0/0
	  SNMP ifindex: 1237
	  Admin state: enabled, Operational state: up, Uptime: 0 days, 00:01:30
	  State transitions: 0, Last cleared: 0 days, 00:01:30
	  Speed: 400Gbps
	  Total Lanes: 8
	  Active Lanes: 8
      Utilization rates (input/output): 50%/90%
      Utilization rate threshold: 100%
	  
	  Flags: C - Non-zero CRC rate, S - Non-zero size error-count, G - Non-zero code group error-count
	         M - Link down, misalignment error, L - Link down, SerDes signal lock error
	         R - Link up, but not accepting reachability cells
	         T - Bad link connectivity or link down, based on reachability cells
	
	  | Lane id       | Operational | Flags   |
	  |---------------+-------------+---------|
	  | 0 (sfi0/0)    | up          |         |
	  | 1 (sfi0/1)    | up          |         |
	  | 2 (sfi0/2)    | up          |         |
	  | 3 (sfi0/3)    | up          |         |
	  | 4 (sfi0/4)    | up          |         |
	  | 5 (sfi0/5)    | up          |         |
	  | 6 (sfi0/6)    | up          |         |
	  | 7 (sfi0/7)    | up          |         |
	

.. **Help line:** show fabric interface list

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 11.0    | Command introduced                                         |
+---------+------------------------------------------------------------+
| 11.2    | Output updated                                             |
+---------+------------------------------------------------------------+
| 17.2    | Added interface operational status transitions information |
+---------+------------------------------------------------------------+
