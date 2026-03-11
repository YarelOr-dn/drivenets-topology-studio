show bgp link-state 
--------------------

**Minimum user role:** viewer

To display BGP link-state information:


**Command syntax: show bgp link-state** nlri [nlri]

**Command mode:** operational

.. **Note**


**Parameter table**

+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter        | Description                                                                                                                                                       | Range                       |
+==================+===================================================================================================================================================================+=============================+
| nlri             | Filter the displayed information for a specific Network Layer Reachability Information (NLRI). Each link-state NLRI describes either a node, a link, or a prefix. | \-                          |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp link-state
		link-state: 10 destinations, 10 routes (10 active, 0 holddown, 0 hidden)
		+ = Active Route, - = Last Active, * = Both
		
		NODE { AS:65534 iso-network:0102.5502.4211.00 ISIS-L2 }/1152              
		                   *[BGP/170] 00:17:32, localpref 100, from 10.255.105.141
		                      AS path: 65534 I, validation-state: unverified
		                    > to 8.31.1.103 via bundle-1
		NODE { AS:65534 iso-network:0102.5502.4250.00 ISIS-L2 }/1152              
		                   *[BGP/170] 00:17:32, localpref 100, from 10.255.105.141
		                      AS path: 65534 I, validation-state: unverified
		                    > to 8.31.1.103 via bundle-1
		NODE { AS:65534 iso-network:0102.5502.4250.02 ISIS-L2 }/1152              
		                   *[BGP/170] 00:17:32, localpref 100, from 10.255.105.141
		                      AS path: 65534 I, validation-state: unverified
		                    > to 8.31.1.103 via bundle-1
		LINK { Local { AS:65534 iso-network:0102.5502.4211.00 }.{ IPv4:8.42.1.104 } Remote { AS:65534 iso-network:0102.5501.8181.00 }.{ IPv4:8.42.1.102 } ISIS-L2 }/1152              
		                   *[BGP/170] 00:17:32, localpref 100, from 10.255.105.141
		                      AS path: 65534 I, validation-state: unverified
		                    > to 8.31.1.103 via bundle-1
		LINK { Local { AS:65534 iso-network:0102.5502.4211.00 }.{ IPv4:8.64.1.104 } Remote { AS:65534 iso-network:0102.5502.4250.02 }.{ } ISIS-L2:0 }/1152              
		                   *[BGP/170] 00:02:03, localpref 100, from 10.255.105.141
		                      AS path: 65534 I, validation-state: unverified
		                    > to 8.31.1.103 via bundle-1
		
		PREFIX { Node { AS: 65534 iso-network:0102.5502.4211.00 } { IPv4:10.10.10.10/32 } ISIS-L1:0 }/1152              
		                   *[IS-IS/15] 00:01:01
		

	dnRouter# show bgp link-state nlri NODE { AS:65534 iso-network:0102.5502.4211.00 ISIS-L2 }/1152            
		IS-IS instance: INSTANCE_A
		                Level: 2
		                State: <Active NotInstall>
		                Local AS: 65534
		                Hostname: ROUTER_A
		                IPv4 Router-ids:
		                   1.1.1.1
		                iso-network:
		                   0102.5502.4211.00
		                Age: 6:05
		
	
	dnRouter# show bgp link-state nlri LINK { Local { AS:7019 iso-network:1111.1111.1111.00 }.{IPv4:13.13.13.0} Remote { AS:7019 iso-network:3333.3333.3333.00 }.{IPv4:13.13.13.1} ISIS_LEVEL2 }[0x0000]
	
	BGP BGP LS Link-state routing table entry for LINK { Local { AS:7019 iso-network:1111.1111.1111.00 }.{IPv4:13.13.13.0} Remote { AS:7019 iso-network:33
	Paths: (1 available, best #1)
	  Not advertised to any peer
	     Level: 2
	     From: 102.102.102.102
	     Metric: 5555
	     Local IP: 13.13.13.0
	     Remote IP: 13.13.13.1
	     Local AS: 7019
	     Remote AS: 7019
	     Local iso-network: 1111.1111.1111.00
	     Remote iso-network: 3333.3333.3333.00
	     Topology: ipv4-unicast
	     Admin group: 0x40000
	     Max bandwidth: 9223372036854775808
	     Max reserved bandwidth: 0
	     Unreserved bandwidth: 1000000 (Kbps/sec) 0 (Kbps/sec) 1000000 (Kbps/sec) 1000000 (Kbps/sec) 1000000 (Kbps/sec) 0 (Kbps/sec) 1000000 (Kbps/sec) 1000000 (Kbps/sec)
	     Te default metric: 21
	     Last update: 00:03:32
																	

.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+

