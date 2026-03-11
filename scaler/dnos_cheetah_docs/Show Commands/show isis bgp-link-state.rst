show isis bgp-link-state
------------------------

**Minimum user role:** viewer

To display all IS-IS database entries distributed to BGP:

**Command syntax: show isis** instance [isis-instance-name] **bgp-link-state** {nlri [nlri] \| detail}

**Command mode:** operational


..
	**Internal Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when now specified, display information from all isis instances

	- use "nlri" to display detail information matching a specific nlri

	- use detail to display detail information for all entries

**Parameter table**

+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                                                             |
+====================+=========================================================================================================================================================+
| isis-instance-name | Displays BGP link state information for a specific IS-IS instance. If you do not specify an instance, information from all instances will be displayed. |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
| nlri               | Displays detailed information matching a specific NLRI                                                                                                  |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
| detail             | Displays detailed information for all entries                                                                                                           |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show isis bgp-link-state
	Instance REGION_0:
	IS-IS level-2 bgp link state database:
	NODE { AS:15 iso-network:11.1114.1111.11 ISIS_LEVEL2 } last updated:00:02:58
	NODE { AS:15 iso-network:11.1115.1111.11 ISIS_LEVEL2 } last updated:00:02:48
	PREFIX { { AS:15 iso-network:11.1114.1111.11 }[t:0x0000] {1.0.0.0} ISIS_LEVEL2 } last updated:00:02:58
	PREFIX { { AS:15 iso-network:11.1114.1111.11 }[t:0x0000] {3.0.0.0} ISIS_LEVEL2 } last updated:00:02:58
	PREFIX { { AS:15 iso-network:11.1115.1111.11 }[t:0x0000] {1.0.0.0} ISIS_LEVEL2 } last updated:00:02:48
	PREFIX { { AS:15 iso-network:11.1114.1111.11 }[t:0x0000] {101.1.1.0} ISIS_LEVEL2 } last updated:00:02:58
	PREFIX { { AS:15 iso-network:11.1114.1111.11 }[t:0x0000] {44.44.44.44} ISIS_LEVEL2 } last updated:00:02:58
	PREFIX { { AS:15 iso-network:11.1115.1111.11 }[t:0x0000] {55.55.55.55} ISIS_LEVEL2 } last updated:00:02:48
	LINK { Local { AS:15 iso-network:11.1114.1111.11 }. Remote { AS:15 iso-network:11.1115.1111.11 }. ISIS_LEVEL2 } last updated:00:02:48
	LINK { Local { AS:15 iso-network:11.1114.1111.11 }. Remote { AS:15 iso-network:11.1115.1111.11 }. ISIS_LEVEL2 } last updated:00:02:48
	
	
	
	dnRouter# show isis instance REGION_0 bgp-link-state
	Instance REGION_0:
	IS-IS level-2 bgp link state database:
	NODE { AS:15 iso-network:11.1114.1111.11 ISIS_LEVEL2 } last updated:00:02:58
	NODE { AS:15 iso-network:11.1115.1111.11 ISIS_LEVEL2 } last updated:00:02:48
	PREFIX { { AS:15 iso-network:11.1114.1111.11 }[t:0x0000] {1.0.0.0} ISIS_LEVEL2 } last updated:00:02:58
	PREFIX { { AS:15 iso-network:11.1114.1111.11 }[t:0x0000] {3.0.0.0} ISIS_LEVEL2 } last updated:00:02:58
	PREFIX { { AS:15 iso-network:11.1115.1111.11 }[t:0x0000] {1.0.0.0} ISIS_LEVEL2 } last updated:00:02:48
	PREFIX { { AS:15 iso-network:11.1114.1111.11 }[t:0x0000] {101.1.1.0} ISIS_LEVEL2 } last updated:00:02:58
	PREFIX { { AS:15 iso-network:11.1114.1111.11 }[t:0x0000] {44.44.44.44} ISIS_LEVEL2 } last updated:00:02:58
	PREFIX { { AS:15 iso-network:11.1115.1111.11 }[t:0x0000] {55.55.55.55} ISIS_LEVEL2 } last updated:00:02:48
	LINK { Local { AS:15 iso-network:11.1114.1111.11 }. Remote { AS:15 iso-network:11.1115.1111.11 }. ISIS_LEVEL2 } last updated:00:02:48
	LINK { Local { AS:15 iso-network:11.1114.1111.11 }. Remote { AS:15 iso-network:11.1115.1111.11 }. ISIS_LEVEL2 } last updated:00:02:48
	
	
	dnRouter# show isis bgp-link-state nlri PREFIX { { AS:15 iso-network:11.1114.1111.11 }[t:0x0000] {1.0.0.0} ISIS_LEVEL2 }
	Instance REGION_0:
	IS-IS level-2 bgp link state database:
	     Level: 2
	     Metric: 10
	     Local AS: 1
	     Iso-network: 11.1114.1111.11
	     Multi-topology: Not set
	     Flags: None
	     Last update: 00:02:45
	
	dnRouter# show isis bgp-link-state nlri NODE { AS:15 iso-network:11.1114.1111.11 ISIS_LEVEL2 }
	Instance REGION_0:
	IS-IS level-2 bgp link state database:
	     Level: 2
	     Local AS: 1
	     Hostname: q4
	     IPv4 Router-ids: 44.44.44.44
	     Iso-network: 11.1114.1111.11
	     Area(s): 47.0001
	     Flags: None
	     Last update: 00:04:40
	
	
	
	dnRouter# show isis instance REGION_0 bgp-link-state nlri LINK { Local { AS:15 iso-network:11.1114.1111.11 }. Remote { AS:15 iso-network:11.1115.1111.11 }. ISIS_LEVEL2 }
	Instance REGION_0:
	IS-IS level-2 bgp link state database:
	     Level: 2
	     Metric: 10
	     Admin group: 0
	     Local IP: 0.0.0.0
	     Remote IP: 0.0.0.0
	     Local AS: 1
	     Remote AS: 1
	     Local iso-network: 11.1114.1111.11
	     Remote iso-network: 11.1115.1111.11
	     Multi-topology: 0x0000
	     Max bandwidth: 0.000000
	     TE configured: False
	     Last update: 00:07:02
	
	
	
	dnRouter# show isis bgp-link-state detail
	Instance REGION_0:
	IS-IS level-2 bgp link state database:
	     Level: 2
	     Metric: 10
	     Local AS: 1
	     Iso-network: 11.1114.1111.11
	     Multi-topology: Not set
	     Flags: None
	     Last update: 00:02:45
	
	Instance 1:
	IS-IS level-2 bgp link state database:
	     Level: 2
	     Local AS: 1
	     Hostname: q4
	     IPv4 Router-ids: 44.44.44.44
	     Iso-network: 11.1114.1111.11
	     Area(s): 47.0001
	     Flags: None
	     Last update: 00:04:40
	
	Instance REGION_1:
	IS-IS level-2 bgp link state database:
	     Level: 2
	     Metric: 10
	     Admin group: 0
	     Local IP: 1.0.0.3
	     Remote IP: 1.0.0.4
	     Local AS: 1
	     Remote AS: 1
	     Local iso-network: 11.1114.1111.11
	     Remote iso-network: 11.1115.1111.11
	     Multi-topology: 0x0000
	     Max bandwidth: 0.000000
	     TE configured: True
	     Last update: 00:00:42


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+

