show bgp flowspec neighbors advertised-routes
---------------------------------------------

**Minimum user role:** viewer

To display advertised routes under flowspec neighbors sessions:

**Command syntax: show bgp** instance vrf [vrf-name] **[address-family] flowspec neighbors [neighbor-address] advertised-routes** nlri [nlri]

**Command mode:** operational



**Note**

- Use "nlri" to display detailed information matching a specific NLRI.

- Use quotation marks for NLRI strings.

**Parameter table**

+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter         | Description                                                                                                                                                       | Range                       |
+===================+===================================================================================================================================================================+=============================+
| vrf-name          | Display routing information for a non-default VRF                                                                                                                 | 1..255 characters           |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family    | Display routing information for a specific address-family (AFI)                                                                                                   | IPv4                        |
|                   |                                                                                                                                                                   | IPv6                        |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| neighbor-address  | Neighbor address                                                                                                                                                  | A.B.C.D                     |
|                   |                                                                                                                                                                   | xx:xx::xx:xx                |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| advertised-routes | Displays the routes advertised to a BGP neighbor                                                                                                                  | \-                          |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| nlri              | Filter the displayed information for a specific Network Layer Reachability Information (NLRI).                                                                    | \-                          |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

    dnRouter# show bgp ipv4 flowspec neighbors 1.1.1.1 advertised-routes
    BGP Adj-out table entry for DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
    1
      192.168.1.2
     Origin IGP, metric 0, localpref 100
     Extended Community: flowspec-redirect-ip-nh:0 flowspec-traffic-rate:1:500

    pe1# show bgp ipv4 flowspec neighbors 192.168.1.3 advertised-routes nlri "DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5"
    BGP Adj-out table entry for DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
    1
      192.168.1.2
     Origin IGP, metric 0, localpref 100
     Extended Community: flowspec-redirect-ip-nh:0 flowspec-traffic-rate:1:500

.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 13.0    | Command introduced                 |
+---------+------------------------------------+

