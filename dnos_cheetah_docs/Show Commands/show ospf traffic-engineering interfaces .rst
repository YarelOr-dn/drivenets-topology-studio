show ospf traffic-engineering interfaces
----------------------------------------

**Minimum user role:** viewer

DIsplays the OSPF traffic-engineering information for interfaces.



**Command syntax: show ospf traffic-engineering interfaces** [interface-name]

**Command mode:** operational



..
	**Internal Note**

	- Indicate a specific interface-name to filter result for that interface

**Parameter table**

+----------------+---------------------------+----------------------------------+---------------+
| Parameter      | Description               | Range                            | Default       |
+================+===========================+==================================+===============+
| interface-name | The name of the interface | ge{/10/25/40/100}-X/Y/Z          |               |
|                |                           | bundle-<bundle-id>               | \-            |
|                |                           | bundle-<bundle-id.sub-bundle-id> |               |
+----------------+---------------------------+----------------------------------+---------------+

**Example**
::

	dnRouter# show ospf traffic-engineering interfaces

	 -- MPLS-TE link parameters for bundle-1 --
	    Administrative Group: 0x0
	    Local Interface IP Address(es): 12.3.0.10
	    Maximum Bandwidth: 10000 (kbit/sec)
	    Maximum Reservable Bandwidth: 10000 (kbit/sec)
	    Unreserved Bandwidth:
	      [0]: 10000 (kbit/sec),	[1]: 10000 (kbit/sec)
	      [2]: 10000 (kbit/sec),	[3]: 10000 (kbit/sec)
	      [4]: 10000 (kbit/sec),	[5]: 10000 (kbit/sec)
	      [6]: 10000 (kbit/sec),	[7]: 10000 (kbit/sec)

	-- MPLS-TE link parameters for bundle-2 --
	    Administrative Group: 0x0
	    Local Interface IP Address(es): 13.0.0.10
	    Remote Interface IP Address(es): 13.0.0.3
	    Maximum Bandwidth: 10000 (kbit/sec)
	    Maximum Reservable Bandwidth: 10000 (kbit/sec)
	    Unreserved Bandwidth:
	      [0]: 10000 (kbit/sec),	[1]: 10000 (kbit/sec)
	      [2]: 10000 (kbit/sec),	[3]: 10000 (kbit/sec)
	      [4]: 10000 (kbit/sec),	[5]: 10000 (kbit/sec)
	      [6]: 10000 (kbit/sec),	[7]: 10000 (kbit/sec)


	dnRouter# show ospf traffic-engineering interfaces bundle-1
	-- MPLS-TE link parameters for eth1 --
	    Administrative Group: 0x0
	    Local Interface IP Address(es): 12.3.0.10
	    Maximum Bandwidth: 10000 (kbit/sec)
	    Maximum Reservable Bandwidth: 10000 (kbit/sec)
	    Unreserved Bandwidth:
	      [0]: 10000 (kbit/sec),	[1]: 10000 (kbit/sec)
	      [2]: 10000 (kbit/sec),	[3]: 10000 (kbit/sec)
	      [4]: 10000 (kbit/sec),	[5]: 10000 (kbit/sec)
	      [6]: 10000 (kbit/sec),	[7]: 10000 (kbit/sec)

.. **Help line:** Displays OSPF interfaces traffic-engineering information.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
