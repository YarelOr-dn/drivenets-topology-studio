show isis traffic-engineering interfaces
----------------------------------------

**Minimum user role:** viewer

This command is applicable to the following interfaces:

physical interfaces bundle interfaces bundle sub-interfaces

To display the IS-IS interfaces with traffic engineering enabled:

**Command syntax: show isis** instance [isis-instance-name] **traffic-engineering interfaces** [interface-name]

**Command mode:** operational



.. **Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when not specified, display information from all isis instances

	- set interface-name to filter result for a specific interface

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                            |
+====================+========================================================================================================+
| No filter          | Displays all the interfaces that are enabled for traffic-engineering.                                  |
+--------------------+--------------------------------------------------------------------------------------------------------+
| isis-instance-name | Displays only the interfaces that are enabled for traffic-engineering for the specified IS-IS instance |
+--------------------+--------------------------------------------------------------------------------------------------------+
| interface-name     | Filters the information for a specific interface.                                                      |
+--------------------+--------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show isis traffic-engineering interfaces 
	 -- MPLS-TE link parameters for bundle-1 --
	    Administrative Group: 0x0
	    Local Interface IP Address(es): 12.3.0.10
	    Maximum Bandwidth: 10000 (kbit/sec)
	    Maximum Reservable Bandwidth: 10000 (Bytes/sec)
	    Unreserved Bandwidth:
	      [0]: 10000 (kbit/sec),	[1]: 10000 (kbit/sec)
	      [2]: 10000 (kbit/sec),	[3]: 10000 (kbit/sec)
	      [4]: 10000 (kbit/sec),	[5]: 10000 (kbit/sec)
	      [6]: 10000 (kbit/sec),	[7]: 10000 (kbit/sec)
	    ---------------
	
	-- MPLS-TE link parameters for bundle-2 --
	    Administrative Group: 0x0
	    Local Interface IP Address(es): 13.0.0.10
	    Remote Interface IP Address(es): 13.0.0.3
	    Maximum Bandwidth: 10000 (kbit/sec)
	    Maximum Reservable Bandwidth: 10000 (Bytes/sec)
	    Unreserved Bandwidth:
	      [0]: 10000 (kbit/sec),	[1]: 10000 (kbit/sec)
	      [2]: 10000 (kbit/sec),	[3]: 10000 (kbit/sec)
	      [4]: 10000 (kbit/sec),	[5]: 10000 (kbit/sec)
	      [6]: 10000 (kbit/sec),	[7]: 10000 (kbit/sec)
	---------------
	
	  lo: MPLS-TE is disabled on this interface
	
	
	dnRouter# show isis traffic-engineering interfaces bundle-1
	-- MPLS-TE link parameters for eth1 --
	    Administrative Group: 0x0
	    Local Interface IP Address(es): 12.3.0.10
	    Maximum Bandwidth: 10000 (kbit/sec)
	    Maximum Reservable Bandwidth: 10000 (Bytes/sec)
	    Unreserved Bandwidth:
	      [0]: 10000 (kbit/sec),	[1]: 10000 (kbit/sec)
	      [2]: 10000 (kbit/sec),	[3]: 10000 (kbit/sec)
	      [4]: 10000 (kbit/sec),	[5]: 10000 (kbit/sec)
	      [6]: 10000 (kbit/sec),	[7]: 10000 (kbit/sec)
	---------------
	
	dnRouter# show isis instance CORE traffic-engineering interfaces 
	
	

.. **Help line:**

**Command History**

+---------+---------------------------------+
| Release | Modification                    |
+=========+=================================+
| 9.0     | Command introduced              |
+---------+---------------------------------+
| 10.0    | Added filter per IS-IS instance |
+---------+---------------------------------+


