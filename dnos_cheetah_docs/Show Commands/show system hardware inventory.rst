show system hardware inventory
------------------------------

**Minimum user role:** viewer

System hardware inventory displays the currently available hardware inventory, per node or all nodes in a cluster and/or transceivers.



**Command syntax: show system hardware inventory** [node-name] [node-id] {[transceivers] | [detail]}

**Command mode:** operational



**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                                                                                                | Range            | Default |
+===========+============================================================================================================================================+==================+=========+
| node-name | The name of the node used to filter the output to a specific cluster element. If no name is provided, all cluster nodes will be displayed. | NCP              | \-      |
|           |                                                                                                                                            | NCF              |         |
|           |                                                                                                                                            | NCC              |         |
|           |                                                                                                                                            | NCM              |         |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+------------------+---------+
| node-id   | The ID of the node used to filter the output to a specific cluster element.                                                                | NCP: 0..249      | \-      |
|           |                                                                                                                                            | NCC: 0..1        |         |
|           |                                                                                                                                            | NCF: 0..611      |         |
|           |                                                                                                                                            | NCM A0-1, B0-1   |         |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+------------------+---------+

**Example**
::

	dnRouter# show system hardware inventory

	ncc 0 (dn-ncc-0)
	Model: X86
	Hardware Model: ProLiant DL380 Gen10
	Hardware Revision: N/A
	Serial Number: ABCDE1001
	CPU Model: Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz
	Power Supply Units:
	  | PSU ID | Serial         | Revision  | Type         |
	  |--------+----------------+-----------+--------------|
	  | 0      | 5WBXU0DLLBM3XA | 1.0       | AC 100-240 V |
	  | 1      | 5WBXU0DLLBM3H4 | 1.0       | AC 100-240 V |

	Ethernet Controller Model:
	  | NIC              | Serial             | Description                                     |
	  |------------------+--------------------+-------------------------------------------------|
	  | 1 (ctrl-0)       | MT1943K06807       | MT27800 Family [ConnectX-5]                     |
	  | 2 (ctrl-1)       | MT1943K06808       | MT27800 Family [ConnectX-5]                     |

	ncp 0 (dn-ncp-0)
	Model: NCP-40C
	Hardware Model: S9700-53DX
	Hardware Revision: 2, Build: 4
	Serial Number: ABCDE1001
	CPU Model: Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz
	Power Supply Units:
	  | PSU ID | Serial         | Revision  | Type         |
	  |--------+----------------+-----------+--------------|
	  | 0      | 5WBXU0DLLBM3XA | 1.0       | AC 100-240 V |
	  | 1      | 5WBXU0DLLBM3H4 | 1.0       | AC 100-240 V |

	ncf 0 (dn-ncf-0)
	Model: NCF-48CD
	Hardware Model: S9705-48D
	Hardware Revision: 2, Build: 4
	Serial Number: ABCDE1001
	CPU Model: Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz
	Power Supply Units:
	  | PSU ID | Serial         | Revision  | Type         |
	  |--------+----------------+-----------+--------------|
	  | 0      | 5WBXU0DLLBM3XA | 1.0       | AC 100-240 V |
	  | 1      | 5WBXU0DLLBM3H4 | 1.0       | AC 100-240 V |

	ncm A0 (dn-ncm-A0)
	Model: NCP48X-6C
	Hardware Model: AS5916-54XL-OT
	Hardware Revision: N/A
	Serial Number: ABCDE1001
	CPU Model: Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz
	Power Supply Units:
	  | PSU ID | Serial         | Revision  | Type         |
	  |--------+----------------+-----------+--------------|
	  | 0      | 5WBXU0DLLBM3XA | 1.0       | AC 100-240 V |
	  | 1      | 5WBXU0DLLBM3H4 | 1.0       | AC 100-240 V |

	dnRouter# show system hardware inventory ncc 0

	ncc 0 (dn-ncc-0)
	Model: X86
	Hardware Model: ProLiant DL380 Gen10
	Hardware Revision: N/A
	Serial Number: ABCDE1001
	CPU Model: Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz
	Power Supply Units:
	  | PSU ID | Serial         | Revision  | Type         |
	  |--------+----------------+-----------+--------------|
	  | 0      | 5WBXU0DLLBM3XA | 1.0       | AC 100-240 V |
	  | 1      | 5WBXU0DLLBM3H4 | 1.0       | AC 100-240 V |

	Ethernet Controller Model:
	  | NIC              | Serial             | Description                                     |
	  |------------------+--------------------+-------------------------------------------------|
	  | 1 (ctrl-0)       | MT1943K06807       | MT27800 Family [ConnectX-5]                     |
	  | 2 (ctrl-1)       | MT1943K06808       | MT27800 Family [ConnectX-5]                     |

	dnRouter# show system hardware inventory ncc 0 transceivers

	Network interfaces transceivers: N/A
	Fabric interfaces transceivers: N/A
	Control interfaces transceivers:
	ctrl-ncc-0/0
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	ctrl-ncc-0/1
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065


	dnRouter# show system hardware inventory ncp 0 detail

	ncp 0 (dn-ncp-0)
	Model: NCP-40C
	Hardware Model: S9700-53DX
	Hardware Revision: 2, Build: 4
	Serial Number: ABCDE1001
	CPU Model: Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz
	Power Supply Units:
	  | PSU ID | Serial         | Revision  | Type         |
	  |--------+----------------+-----------+--------------|
	  | 0      | 5WBXU0DLLBM3XA | 1.0       | AC 100-240 V |
	  | 1      | 5WBXU0DLLBM3H4 | 1.0       | AC 100-240 V |

	Network interfaces transceivers:
	ge100-0/0/0
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	ge100-0/0/1
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	Fabric interfaces transceivers:
	fab-ncp400-0/0/0
		Identifier                                : QSFP_DD
		Vendor name                               : INNOLIGHT
		Vendor OUI                                : 44:7C:7F
		Vendor PN                                 : C-DQ8FNM010-N00
		Vendor rev                                : 1A
		Vendor SN                                 : INJAQ8090025B
		Firmware version                          : 61.22

	Control interfaces transceivers:
	ctrl-ncp-0/0
		Identifier                                : QSFP
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	dnRouter# show system hardware inventory detail

	ncc 0 (dn-ncc-0)
	Model: X86
	Hardware Model: ProLiant DL380 Gen10
	Hardware Revision: N/A
	Serial Number: ABCDE1001
	CPU Model: Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz
	Power Supply Units:
	  | PSU ID | Serial         | Revision  | Type         |
	  |--------+----------------+-----------+--------------|
	  | 0      | 5WBXU0DLLBM3XA | 1.0       | AC 100-240 V |
	  | 1      | 5WBXU0DLLBM3H4 | 1.0       | AC 100-240 V |

	Ethernet Controller Model:
	  | NIC              | Serial             | Description                                     |
	  |------------------+--------------------+-------------------------------------------------|
	  | 1 (ctrl-0)       | MT1943K06807       | MT27800 Family [ConnectX-5]                     |
	  | 2 (ctrl-1)       | MT1943K06808       | MT27800 Family [ConnectX-5]                     |

	Network interfaces transceivers: N/A
	Fabric interfaces transceivers: N/A
	Control interfaces transceivers:
	ctrl-ncc-0/0
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	ctrl-ncc-0/1
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	ncp 0 (dn-ncp-0)
	Model: NCP-40C
	Hardware Model: S9700-53DX
	Hardware Revision: 2, Build: 4
	Serial Number: ABCDE1001
	CPU Model: Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz

	Disk Information:
	  | Location      | Capacity  | Model               | Serial                    |
	  |---------------+-----------+---------------------+---------------------------|
	  | 1             | 128GB     | ATP I-Temp M.2 2280 | 99001190924000000053      |

	Power Supply Units:
	  | PSU ID | Serial         | Revision  | Type         |
	  |--------+----------------+-----------+--------------|
	  | 0      | 5WBXU0DLLBM3XA | 1.0       | AC 100-240 V |
	  | 1      | 5WBXU0DLLBM3H4 | 1.0       | AC 100-240 V |

	Network interfaces transceivers:
	ge100-0/0/0
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	ge100-0/0/1
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	Fabric interfaces transceivers:
	fab-ncp400-0/0/0
		Identifier                                : QSFP_DD
		Vendor name                               : INNOLIGHT
		Vendor OUI                                : 44:7C:7F
		Vendor PN                                 : C-DQ8FNM010-N00
		Vendor rev                                : 1A
		Vendor SN                                 : INJAQ8090025B
		Firmware version                          : 61.22

	Control interfaces transceivers:
	ctrl-ncp-0/0
		Identifier                                : QSFP
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	ncf 0 (dn-ncf-0)
	Model: NCF-48CD
	Hardware Model: S9705-48D
	Hardware Revision: 2, Build: 4
	Serial Number: ABCDE1001
	CPU Model: Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz
	Power Supply Units:
	  | PSU ID | Serial         | Revision  | Type         |
	  |--------+----------------+-----------+--------------|
	  | 0      | 5WBXU0DLLBM3XA | 1.0       | AC 100-240 V |
	  | 1      | 5WBXU0DLLBM3H4 | 1.0       | AC 100-240 V |

	Network interfaces transceivers: N/A
	Fabric interfaces transceivers:
	fab-ncf400-0/0/0
		Identifier                                : QSFP_DD
		Vendor name                               : INNOLIGHT
		Vendor OUI                                : 44:7C:7F
		Vendor PN                                 : C-DQ8FNM010-N00
		Vendor rev                                : 1A
		Vendor SN                                 : INJAQ8090025B
		Firmware version                          : 61.22

	Control interfaces transceivers: N/A

	ncm A0 (dn-ncm-A0)
	Model: NCP48X-6C
	Hardware Model: AS5916-54XL-OT
	Hardware Revision: N/A
	Serial Number: ABCDE1001
	CPU Model: Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz
	Power Supply Units:
	  | PSU ID | Serial         | Revision  | Type         |
	  |--------+----------------+-----------+--------------|
	  | 0      | 5WBXU0DLLBM3XA | 1.0       | AC 100-240 V |
	  | 1      | 5WBXU0DLLBM3H4 | 1.0       | AC 100-240 V |

	Network interfaces transceivers: N/A
	Fabric interfaces transceivers: N/A
	Control interfaces transceivers:
	ctrl-ncm-A0/0
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	dnRouter# show system hardware inventory transceivers

	ncc 0 (dn-ncc-0)
	Network interfaces transceivers: N/A
	Fabric interfaces transceivers: N/A
	Control interfaces transceivers:
	ctrl-ncc-0/0
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	ctrl-ncc-0/1
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	ncp 0 (dn-ncp-0)
	Network interfaces transceivers:
	ge100-0/0/0
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	ge100-0/0/1
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	Fabric interfaces transceivers:
	fab-ncp400-0/0/0
		Identifier                                : QSFP_DD
		Vendor name                               : INNOLIGHT
		Vendor OUI                                : 44:7C:7F
		Vendor PN                                 : C-DQ8FNM010-N00
		Vendor rev                                : 1A
		Vendor SN                                 : INJAQ8090025B
		Firmware version                          : 61.22

	Control interfaces transceivers:
	ctrl-ncp-0/0
		Identifier                                : QSFP
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

	ncf 0 (dn-ncf-0)
	Network interfaces transceivers: N/A
	Fabric interfaces transceivers:
	fab-ncf400-0/0/0
		Identifier                                : QSFP_DD
		Vendor name                               : INNOLIGHT
		Vendor OUI                                : 44:7C:7F
		Vendor PN                                 : C-DQ8FNM010-N00
		Vendor rev                                : 1A
		Vendor SN                                 : INJAQ8090025B
		Firmware version                          : 61.22

	Control interfaces transceivers: N/A

	ncm A0 (dn-ncm-A0)
	Network interfaces transceivers: N/A
	Fabric interfaces transceivers: N/A
	Control interfaces transceivers:
	ctrl-ncm-A0/0
		Identifier                                : QSFP28
		Vendor name                               : Mellanox
		Vendor OUI                                : 00:02:c9
		Vendor PN                                 : MMA1B00-C100D
		Vendor rev                                : A3
		Vendor SN                                 : MT1652FT00065

.. **Help line:** show system hardware inventory

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 13.2    | Command introduced                            |
+---------+-----------------------------------------------+
| 17.1    | Added firmware version for CMIS 4.0 and newer |
+---------+-----------------------------------------------+
