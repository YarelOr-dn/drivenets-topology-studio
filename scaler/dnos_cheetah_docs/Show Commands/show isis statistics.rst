show isis statistics
--------------------

**Minimum user role:** viewer

To display IS-IS statistics information:



**Command syntax: show isis** instance [isis-instance-name] **statistics** interface [interface-name]

**Command mode:** operational



.. **Note**

	-  use "instance [isis-instance-name]" to display information from a specific ISIS instance, when now specified, display information from all isis instances

	-  When instance and interface are used, expected to auto complete only interfaces configured to that instance

**Parameter table**

+--------------------+-----------------------------------------------------------------------------------------------------------------------------------------+---------+
| Parameter          | Description                                                                                                                             | Range   |
+====================+=========================================================================================================================================+=========+
| isis-instance-name | Displays statistics for a specific IS-IS instance. If you do not specify an instance, information from all instances will be displayed. | String  |
+--------------------+-----------------------------------------------------------------------------------------------------------------------------------------+---------+
| level              | Filter the displayed information for a specific level                                                                                   | Level-1 |
|                    |                                                                                                                                         | Level-2 |
+--------------------+-----------------------------------------------------------------------------------------------------------------------------------------+---------+

The following information is displayed per instance. The information reflects count since instance start or instance clear statistics:

+-------------------+-----------------------------------------------------+
| Field             | Description                                         |
+===================+=====================================================+
| PDU Type          | The IS-IS PDU (LSP, Hello, CSNP, PSNP)              |
+-------------------+-----------------------------------------------------+
| Received          | The total number of PDUs received                   |
+-------------------+-----------------------------------------------------+
| Drops             | The total number of PDU drops due to PDU error      |
+-------------------+-----------------------------------------------------+
| Sent              | The total number of PDUs sent                       |
+-------------------+-----------------------------------------------------+
| SPF runs          | The number of SPF calculations (per address-family) |
+-------------------+-----------------------------------------------------+
| LSP regenerations | The number of regenerated LSPs due to end-of-life   |
+-------------------+-----------------------------------------------------+

**Example**
::

	dnRouter# show isis statistics

	ISIS statistics for instance INST_1:
	  Level-1 statistics
	    PDU type    Received    Drops    Rcv Errors     Sent
	    LSP         91          2        1              9010
	    HELLO       238101      0        0              2286944
	    CSNP        26225       0        0              1
	    PSNP        193         0        0              91
	    Total       264610      2        1              2296046

	    SPF ipv4 runs: 221
	    SPF shortcuts ipv4 runs: 221
	    SPF ipv6 runs: 220
	    LSP regenerations: 134

	  Level-2 statistics
	    PDU type    Received    Drops    Rcv Errors    Sent
	    LSP         792901      145      13            21131274
	    HELLO       2304612     12       0             2278863
	    CSNP        33996       0        0             279
	    PSNP        1298895     0        0             177564
	    Total       4430404     157      13            23587980

	    SPF ipv4 runs: 2526
	    SPF shortcuts ipv4 runs: 2526
	    SPF ipv6 runs: 2525
	    LSP regenerations: 120

	ISIS statistics for instance INST_2:
	  Level-2 statistics
	    PDU type    Received    Drops    Rcv Errors   Sent
	    LSP         435         0        0            94
	    HELLO       8232        1        0            8082
	    CSNP        1           0        0            1
	    PSNP        92          0        0            435
	    Total       8760        1        0            8612

	    SPF ipv4 runs: 523
	    SPF shortcuts ipv4 runs: 523
	    SPF ipv6 runs: 522
	    LSP regenerations: 91

	dnRouter# show isis statistics instance INST_2

	ISIS statistics for instance INST_2:
	  Level-2 statistics
	    PDU type    Received    Drops    Rcv Errors   Sent
	    LSP         435         0        0            94
	    HELLO       8232        1        0            8082
	    CSNP        1           0        0            1
	    PSNP        92          0        0            435
	    Total       8760        1        0            8612

	    SPF ipv4 runs: 523
	    SPF shortcuts ipv4 runs: 523
	    SPF ipv6 runs: 522
	    LSP regenerations: 91

	dnRouter# show isis statistics interface bundle-1

	ISIS statistics for instance INST_1 interface bundle-1:
	  Level-1 statistics
	    PDU type    Received    Drops    Sent
	    LSP         91          2        9010
	    HELLO       238101      0        2286944
	    CSNP        26225       0        1
	    PSNP        193         0        91
	    UNKNOWN     0           0        0
	    Total       264610      2        2296046

	  Level-2 statistics
	    PDU type    Received    Drops    Sent
	    LSP         792901      145      21131274
	    HELLO       2304612     12       2278863
	    CSNP        33996       0        279
	    PSNP        1298895     0        177564
	    UNKNOWN     0           0        0
	    Total       4430404     157      23587980

.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
| 14.0    | Added level filter |
+---------+--------------------+
