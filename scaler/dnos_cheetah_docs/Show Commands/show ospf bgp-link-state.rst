show ospf bgp-link-state
------------------------

**Minimum user role:** viewer

To display all OSPF database entries distributed to BGP:

**Command syntax: show ospf** instance [ospf-instance-name] **bgp-link-state** {nlri [nlri] \| detail}

**Command mode:** operational


..
	**Internal Note**

	- use "instance [ospf-instance-name]" to display information from a specific OSPF instance, when now specified, display information from all ospf instances

	- use "nlri" to display detail information matching a specific nlri

	- use detail to display detail information for all entries

**Parameter table**

+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                                                             |
+====================+=========================================================================================================================================================+
| ospf-instance-name | Displays BGP link state information for a specific IS-IS instance. If you do not specify an instance, information from all instances will be displayed. |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
| nlri               | Displays detailed information matching a specific NLRI                                                                                                  |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
| detail             | Displays detailed information for all entries                                                                                                           |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	q3# show ospf bgp-link-state
	Instance 1:
	OSPF bgp link state database:
	NODE { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 OSPF_V2:1 } last updated:00:01:35
	NODE { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 OSPF_V2:1 } last updated:00:01:29
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }[t:0x0000] {34.0.0.0/24 O} OSPF_V2:1 } last updated:00:01:24
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }[t:0x0000] {34.0.0.0/24 O} OSPF_V2:1 } last updated:00:01:29
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }[t:0x0000] {45.1.0.0/24 IA} OSPF_V2:1 } last updated:00:01:29
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }[t:0x0000] {45.2.0.0/24 IA} OSPF_V2:1 } last updated:00:01:29
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }[t:0x0000] {33.33.33.33/32 O} OSPF_V2:1 } last updated:00:01:35
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }[t:0x0000] {44.44.44.44/32 O} OSPF_V2:1 } last updated:00:01:29
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }[t:0x0000] {55.55.55.55/32 IA} OSPF_V2:1 } last updated:00:01:19
	LINK { Local { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }.{IPv4:34.0.0.3} Remote { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }.{IPv4:34.0.0.4} OSPF_V2:1 }[0x0000] last updated:00:01:19
	LINK { Local { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }.{IPv4:34.0.0.4} Remote { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }.{IPv4:34.0.0.3} OSPF_V2:1 }[0x0000] last updated:00:01:1



	q3# show ospf instance 1 bgp-link-state
	Instance 1:
	OSPF bgp link state database:
	NODE { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 OSPF_V2:1 } last updated:00:01:35
	NODE { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 OSPF_V2:1 } last updated:00:01:29
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }[t:0x0000] {34.0.0.0/24 O} OSPF_V2:1 } last updated:00:01:24
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }[t:0x0000] {34.0.0.0/24 O} OSPF_V2:1 } last updated:00:01:29
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }[t:0x0000] {45.1.0.0/24 IA} OSPF_V2:1 } last updated:00:01:29
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }[t:0x0000] {45.2.0.0/24 IA} OSPF_V2:1 } last updated:00:01:29
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }[t:0x0000] {33.33.33.33/32 O} OSPF_V2:1 } last updated:00:01:35
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }[t:0x0000] {44.44.44.44/32 O} OSPF_V2:1 } last updated:00:01:29
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }[t:0x0000] {55.55.55.55/32 IA} OSPF_V2:1 } last updated:00:01:19
	LINK { Local { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }.{IPv4:34.0.0.3} Remote { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }.{IPv4:34.0.0.4} OSPF_V2:1 }[0x0000] last updated:00:01:19
	LINK { Local { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }.{IPv4:34.0.0.4} Remote { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }.{IPv4:34.0.0.3} OSPF_V2:1 }[0x0000] last updated:00:01:1


	dnRouter# show ospf bgp-link-state nlri PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }[t:0x0000] {34.0.0.0/24 O} OSPF_V2:1 }
	Instance 1:
	OSPF bgp link state database:
	NODE { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 OSPF_V2:1 }
		Protocol: OSPF_V2
		Local AS: 1
		Bgpls-id: 33.33.33.33
		IPv4 Router-ids: 33.33.33.33
		OSPF Area-id: 1.1.1.1
		Hostname:
		Topologies: ipv4-unicast
		Flags: None
		Last update: 00:05:10

	dnRouter# show ospf bgp-link-state nlri PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }[t:0x0000] {34.0.0.0/24 O} OSPF_V2:1 }
	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }[t:0x0000] {34.0.0.0/24 O} OSPF_V2:1 }
		Protocol: OSPF_V2
		Local AS: 1
		Bgpls-id: 33.33.33.33
		IPv4 Router-ids: 33.33.33.33
		OSPF Area-id: 1.1.1.1
		Metric: 65535
		Multi-topology: ipv4 unicast
		Flags: None
		Last update: 00:05:47



	dnRouter# show ospf instance REGION_0 bgp-link-state nlri LINK { Local { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }.{IPv4:34.0.0.3} Remote { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }.{IPv4:34.0.0.4} OSPF_V2:1 }[0x0000]
	LINK { Local { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }.{IPv4:34.0.0.3} Remote { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }.{IPv4:34.0.0.4} OSPF_V2:1 }[0x0000]
		Protocol: OSPF_V2
		Metric: 65535
		Bgpls-id: 33.33.33.33
		Local IP: 34.0.0.3
		Remote IP: 34.0.0.4
		Local AS: 1
		Remote AS: 1
		Local router IP: 33.33.33.33
		Remote router IP: 44.44.44.44
		Admin group: 0x10
		Max bandwidth: 160 Kbps
		Max reserved bandwidth: 120 Kbps
		Unreserved bandwidth: [0] 120 Kbps [1] 120 Kbps [2] 120 Kbps [3] 120 Kbps [4] 120 Kbps [5] 120 Kbps [6] 120 Kbps [7] 120 Kbps
		Traffic Engineering Metric: 4294967294
		SRLG: 333
		Last update: 00:06:35



	dnRouter# show ospf bgp-link-state detail
	Instance 1:
	LINK { Local { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }.{IPv4:34.0.0.3} Remote { AS:1 bgpls-id:33.33.33.33 router-id:44.44.44.44 area-id:1.1.1.1 }.{IPv4:34.0.0.4} OSPF_V2:1 }[0x0000]
		Protocol: OSPF_V2
		Metric: 65535
		Bgpls-id: 33.33.33.33
		Local IP: 34.0.0.3
		Remote IP: 34.0.0.4
		Local AS: 1
		Remote AS: 1
		Local router IP: 33.33.33.33
		Remote router IP: 44.44.44.44
		Admin group: 0x10
		Max bandwidth: 160 Kbps
		Max reserved bandwidth: 120 Kbps
		Unreserved bandwidth: [0] 120 Kbps [1] 120 Kbps [2] 120 Kbps [3] 120 Kbps [4] 120 Kbps [5] 120 Kbps [6] 120 Kbps [7] 120 Kbps
		Traffic Engineering Metric: 4294967294
		SRLG: 333
		Last update: 00:06:35

	NODE { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 OSPF_V2:1 }
		Protocol: OSPF_V2
		Local AS: 1
		Bgpls-id: 33.33.33.33
		IPv4 Router-ids: 33.33.33.33
		OSPF Area-id: 1.1.1.1
		Hostname:
		Topologies: ipv4-unicast
		Flags: None
		Last update: 00:05:10

	PREFIX { { AS:1 bgpls-id:33.33.33.33 router-id:33.33.33.33 area-id:1.1.1.1 }[t:0x0000] {34.0.0.0/24 O} OSPF_V2:1 }
		Protocol: OSPF_V2
		Local AS: 1
		Bgpls-id: 33.33.33.33
		IPv4 Router-ids: 33.33.33.33
		OSPF Area-id: 1.1.1.1
		Metric: 65535
		Multi-topology: ipv4 unicast
		Flags: None
		Last update: 00:05:47




**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+

