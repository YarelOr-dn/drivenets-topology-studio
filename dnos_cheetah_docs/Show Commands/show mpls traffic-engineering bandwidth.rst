show mpls traffic-engineering bandwidth
---------------------------------------

**Minimum user role:** viewer

**Command syntax: show mpls traffic-engineering bandwidth** {interface [interface-name] | detail}

**Command mode:** operational

**Note**

- The command is applicable to the following interface types:
	- Physical
	- Physical vlan
	- Bundle
	- Bundle vlan

**Parameter table**

To display traffic-engineering bandwidth information for every enabled interface:

+----------------+-------------------------------------------------------------------------------+
| Parameter      | Description                                                                   |
+================+===============================================================================+
| no filter      | Displays bandwidth information for all traffic-engineering enabled interfaces |
+----------------+-------------------------------------------------------------------------------+
| interface-name | Displays detailed bandwidth reservation information for the named interface   |
+----------------+-------------------------------------------------------------------------------+
| detail         | Displays detailed information for all interfaces                              |
+----------------+-------------------------------------------------------------------------------+

**Example**
::

	when diffserv-te disabled
	dnRouter# show mpls traffic-engineering bandwidth
	Legend: * - Interface Down, & - Shared-cac
	Interface Name        	[Priority]: <Reserved BW>/<Max Reservable BW> [Kbps]
	bundle-1      	[0]: 0/2000  [1]: 0/2000
	                        [2]: 0/2000  [3]: 0/2000
	                        [4]: 0/2000  [5]: 0/2000
	                        [6]: 0/2000  [7]: 0/2000
	bundle-2      	[0]: 0/1000  [1]: 0/1000
	                        [2]: 0/1000  [3]: 0/1000
	                        [4]: 0/1000  [5]: 0/1000
	                        [6]: 0/1000  [7]: 0/1000


	when diffserv-te enabled
	dnRouter# show mpls traffic-engineering bandwidth
	Legend: * - Interface Down, & - Shared-cac
	Interface Name        	[TE-Class]: <Reserved BW>/<Max Reservable BW> [Kbps]
	bundle-1      	[0]: 0/2000  [1]: 0/2000
	                        [2]: 0/2000  [3]: 0/2000
	                        [4]: 0/2000  [5]: 0/2000
	                        [6]: 0/2000  [7]: 0/2000
	bundle-2      	[0]: 0/1000  [1]: 0/1000
	                        [2]: 0/1000  [3]: 0/1000
	                        [4]: 0/1000  [5]: 0/1000
	                        [6]: 0/1000  [7]: 0/1000

	dnRouter# show mpls traffic-engineering bandwidth interface bundle-5
	Interface: bundle-5
	           Reserved BW: 1000000kbps,  Max Reservable BW: 1000000kbps
	           TE-Class 0: Reserved BW: 500000kbps, Max-Reservable BW: 1000000kbps, Reserved by Higher priority: 500000kbps
	           TE-Class 1: Reserved BW: 1000000kbps, Max-Reservable BW: 1000000kbps, Reserved by Higher priority: 500000kbps
	                       LSP  TEST2, Bandwidth: 300000kbps, src: 1.1.1.1, dest: 2.2.2.2, tid: 7, lspid: 22
	                       LSP  TEST1, Bandwidth: 200000kbps, src: 1.1.1.1, dest: 2.2.2.2, tid: 8, lspid: 23
	           TE-Class 2: Reserved BW: 1000000kbps, Max-Reservable BW: 1000000kbps, Reserved by Higher priority: 1000000kbps
	           TE-Class 3: Reserved BW: 1000000kbps, Max-Reservable BW: 1000000kbps, Reserved by Higher priority: 1000000kbps
	           TE-Class 4: Reserved BW: 500000kbps, Max-Reservable BW: 500000kbps, Reserved by Higher priority: 0kbps
	                       LSP  TEST10, Bandwidth: 500000kbps, src: 1.1.1.1, dest: 2.2.2.2, tid: 9, lspid: 24
	           TE-Class 5: Reserved BW: 500000kbps, Max-Reservable BW: 500000kbps, Reserved by Higher priority: 500000kbps
	           TE-Class 6: Reserved BW: 500000kbps, Max-Reservable BW: 500000kbps, Reserved by Higher priority: 500000kbps
	           TE-Class 7: Reserved BW: 500000kbps, Max-Reservable BW: 500000kbps, Reserved by Higher priority: 500000kbps

	dnRouter# show mpls traffic-engineering bandwidth detail

	Interface: bundle-1719.1719
	Reserved BW: 3kbps,  Max Reservable BW: 30000000kbps
	           TE-Class 0: Reserved BW: 3kbps, Max-Reservable BW: 30000000kbps, Reserved by Higher priority: 3kbps
	           TE-Class 1: Reserved BW: 3kbps, Max-Reservable BW: 15000000kbps, Reserved by Higher priority: 0kbps
	                       LSP  tunnel_bypass_link-bundle-319.319_965, Bandwidth: 1kbps, src: 101.0.0.19, dest: 100.0.0.3, tid: 1283, lspid: 6245
	                       LSP  tunnel_bypass_node-bundle-319.319_967, Bandwidth: 1kbps, src: 101.0.0.19, dest: 101.0.0.18, tid: 1285, lspid: 6246
	                       LSP  tunnel_bypass_node-bundle-319.319_968, Bandwidth: 1kbps, src: 101.0.0.19, dest: 100.0.0.2, tid: 1286, lspid: 6244
	           TE-Class 2: Reserved BW: 3kbps, Max-Reservable BW: 15000000kbps, Reserved by Higher priority: 3kbps
	           TE-Class 3: Reserved BW: 3kbps, Max-Reservable BW: 15000000kbps, Reserved by Higher priority: 3kbps
	           TE-Class 4: Reserved BW: 3kbps, Max-Reservable BW: 30000000kbps, Reserved by Higher priority: 3kbps
	           TE-Class 5: Reserved BW: 3kbps, Max-Reservable BW: 30000000kbps, Reserved by Higher priority: 3kbps
	           TE-Class 6: Reserved BW: 3kbps, Max-Reservable BW: 30000000kbps, Reserved by Higher priority: 3kbps
	           TE-Class 7: Reserved BW: 3kbps, Max-Reservable BW: 30000000kbps, Reserved by Higher priority: 3kbps
	Interface: bundle-219.219
	Reserved BW: 39kbps,  Max Reservable BW: 2850000000kbps
	           TE-Class 0: Reserved BW: 0kbps, Max-Reservable BW: 2850000000kbps, Reserved by Higher priority: 0kbps
	           TE-Class 1: Reserved BW: 0kbps, Max-Reservable BW: 2700000000kbps, Reserved by Higher priority: 0kbps
	           TE-Class 2: Reserved BW: 0kbps, Max-Reservable BW: 2700000000kbps, Reserved by Higher priority: 0kbps
	           TE-Class 3: Reserved BW: 0kbps, Max-Reservable BW: 2700000000kbps, Reserved by Higher priority: 0kbps
	           ...

.. **Help line:**

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 9.0     | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
| 10.0    | Updated command output                                              |
+---------+---------------------------------------------------------------------+
| 11.0    | Updated the syntax, removed the detail option                       |
+---------+---------------------------------------------------------------------+
| 11.5    | Added the detail option to display detailed info for all interfaces |
|         | Added the interface keyword to the syntax.                          |
+---------+---------------------------------------------------------------------+


