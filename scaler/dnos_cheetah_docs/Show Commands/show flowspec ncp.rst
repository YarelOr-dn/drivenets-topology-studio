show flowspec ncp
-----------------

**Minimum user role:** viewer

A FlowSpec rule is imposed on the entire system, specifically, on all interfaces that are FlowSpec enabled (see interfaces flowspec). The show flowspec ncp command displays the NLRIs and their status (i.e. whether installed or not) at the NCP level. Typically all NCPs should display the same NLRIs. If not, this indicates a problem at the NCP level (e.g. lack of resources).

To display FlowSpec rules status in NCP:

**Command syntax: show flowspec ncp [ncp-id]**  nlri [nlri]

**Command mode:** operational



**Note**

- nlri requires the use of quotation marks when entering the nlri string.

**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+
| Parameter | Description                                                                                                                                         | Range             |
+===========+=====================================================================================================================================================+===================+
| ncp-id    | The ID of the NCP for which to display the rules                                                                                                    | 0..255 characters |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+
| nlri      | Filters the display to a specific Network Layer Reachability Information (NLRI). Each link-state NLRI describes either a node, a link, or a prefix. | FlowSpec NLRI     |
|           | Use quotation marks for NLRI strings.                                                                                                               |                   |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+

For each NLRI, the following information is displayed:

+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Parameter      | Description                                                                                               | Range                    |
+================+===========================================================================================================+==========================+
| Address-family | The address-family for the                                                                                | IPv4                     |
|                |                                                                                                           | IPv6                     |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Flow           | The FlowSpec rule installed                                                                               | \-                       |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Actions        | The action to take on the flow                                                                            | Traffic-rate: 0 (= drop) |
|                |                                                                                                           | Else, allow              |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Status         | Displays whether or not the NLRI was installed in the data plane. If it was not, the reason is displayed. | Installed                |
|                |                                                                                                           | Not installed            |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+

**Example**
::

	dnRouter# show flowspec ncp 0

	Address-family: IPv4
		Flow: DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
			Actions: Traffic-rate: 0 bps
			Status: Installed
		Flow: DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32,Protocol:=17,DstPort:3784
			Actions: Traffic-rate: 5000 bps
			Status: Not installed, nlri and/or action not supported

	Address-family: IPv6
		Flow: DstPrefix:=2011:11:100:1::/64,SrcPrefix:=1500:1550:5::1/128,NextHeader:=6,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
			Actions: Traffic-rate: 0 bps
			Status: Installed

	dnRouter# show flowspec ncp 0 nlri "DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32,Protocol:=17,DstPort:3784"

	Address-family: IPv4
		Flow: DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32,Protocol:=17,DstPort:3784
			Actions: Traffic-rate: 5000 bps
			Status: Not installed, nlri and/or action not supported


.. **Help line:** show routing table

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


