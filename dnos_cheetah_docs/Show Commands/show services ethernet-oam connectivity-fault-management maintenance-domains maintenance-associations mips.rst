show services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations mips
----------------------------------------------------------------------------------------------------------

**Minimum user role:** viewer

To display information for Connectivity Fault Management Maintenance Intermediate Points:


**Command syntax: show services ethernet-oam connectivity-fault-management maintenance-domains [md-name] maintenance-associations [ma-name] mips** {[mip-name] | all}

**Command mode:** operational

..
	**Internal Note**
	
	-  

**Example**
::

	dnRouter# show services ethernet-oam connectivity-fault-management maintenanace-domains MD1 maintenance-associations MA1 mips

	Connectivity Fault Management Ethernet OAM Maintenance Endpoints:

	Maintenance Domain: MD1, MD-name: MyMD, Type: string, Level: 7
	Maintenance Association: MA1, MA-name: MyMA1, Type: string

	Local MIPs:
	  +--------+-----------------+-------------------+-------------+
	  | MIP    | Interface       | MAC Address       | Admin State |
	  +========+=================+===================+=============+
	  | MyMIP1 | ge100-0/0/0.400 | 7c:fe:90:57:73:10 | disabled    |
	  | MIP-2  | ge100-0/0/1.100 | 7c:fe:90:57:73:10 | enabled     |
	  +--------+-----------------+-------------------+-------------+


	dnRouter# show services ethernet-oam connectivity-fault-management maintenanace-domains MD1 maintenance-associations MA1 mips MyMIP1

	Connectivity Fault Management Ethernet OAM Maintenance Endpoints:

	Maintenance Domain: MD1, MD-name: MyMD, Type: string, Level: 7
	Maintenance Association: MA1, MA-name: MyMA1, Type: string

	Maintenance Intermediate Point MyMIP1
	  Interface: ge100-0/0/0.400, Admin-state: disabled
	  MAC address: 7c:fe:90:57:73:10
	  CFM Statistics:
	    CFM PDU Statistics:
	      +--------------+-------------+-------------+
	      | CFM PDUs     | Sent        | Received    |
	      +--------------+-------------+-------------+
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
	      | Unicast MAC Mismatch       | 0           |
	      +----------------------------+-------------+


	dnRouter# show services ethernet-oam connectivity-fault-management maintenanace-domains MD1 maintenance-associations MA1 mips all

	Connectivity Fault Management Ethernet OAM Maintenance Endpoints:

	Maintenance Domain: MD1, MD-name: MyMD, Type: string, Level: 7
	Maintenance Association: MA1, MA-name: MyMA1, Type: string

	Maintenance Intermediate Point MyMIP1
	  Interface: ge100-0/0/0.400, Admin-state: disabled
	  MAC address: 7c:fe:90:57:73:10
	  CFM Statistics:
	    CFM PDU Statistics:
	      +--------------+-------------+-------------+
	      | CFM PDUs     | Sent        | Received    |
	      +--------------+-------------+-------------+
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
	      | Unicast MAC Mismatch       | 0           |
	      +----------------------------+-------------+

	Maintenance Intermediate Point MIP-2
	  Interface: ge100-0/0/1.100, Admin-state: enabled
	  MAC address: 7c:fe:90:57:73:10
	  CFM Statistics:
	    CFM PDU Statistics:
	      +--------------+-------------+-------------+
	      | CFM PDUs     | Sent        | Received    |
	      +--------------+-------------+-------------+
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
	      | Unicast MAC Mismatch       | 0           |
	      +----------------------------+-------------+


.. **Help line:** Display CFM Maintenance Intermediate Points

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| TBD     | Command introduced        |
+---------+---------------------------+