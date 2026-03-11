show ospfv3
-----------

**Minimum user role:** viewer

The show ospf command displays information on a variety of general OSPF and OSPFv3 configuration information. You can filter the information by parameter and/or by interface name. When filtering by parameter only, the system displays the requested parameter for all interfaces. When filtering by interface name, the information is further filtered to display the parameter configuration for the requested interface only.

**Command syntax: show ospfv3**

**Command mode:** operational



**Parameter table**

The following are the parameters whose value you can display for a specific interface or for all interfaces:

+---------------+---------------------------------------------------------------------------------------------------------------------------------------+
| Parameter     | Description                                                                                                                           |
+===============+=======================================================================================================================================+
| border-router | Displays OSPF information for an area. See show ospf border-router.                                                                   |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------+
| route         | Displays the OSPF routing table, as determined by the most recent SPF calculation. See show ospf route.                               |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------+
| neighbor      | Displays information on OSPF neighbors (all or filtered by interface). See show ospf neighbors and show ospf neighbors detail.        |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------+
| interface     | Displays concentric information on the OSPF process on all OSPF-enabled interfaces or on a named interface. See show ospf interfaces. |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------+
| database      | Display lists of information related to the OSPF database. See show ospfv3 database.                                                  |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

  dnRouter#show ospfv3

   OSPFv3 Routing Process (0) with Router-ID 22.22.22.22
   Running 00:14:33
   Initial SPF scheduling delay 50 millisec(s)
   Minimum hold time between consecutive SPFs 200 millisec(s)
   Maximum hold time between consecutive SPFs 5000 millisec(s)
   Hold time multiplier is currently 1
   SPF algorithm last executed 00:14:28 ago
   Last SPF duration 0 sec 1419 usec
   SPF timer is inactive
   Initial LSA scheduling delay 50 millisec(s)
   Minimum hold time between consecutive LSA generation 200 millisec(s)
   Maximum hold time between consecutive LSA generation 5000 millisec(s)
   Refresh timer 1800 secs
   Maximum ECMP paths 32
   Auto-Cost reference-bandwidth: 100mbps
   Graceful-Restart:
        Restarting-mode:
          Admin state: enabled
          Grace period: 120 secs
          Grace interval: 60 secs
        Helper-mode:
          Admin state: enabled
   Number of AS scoped LSAs is 0
          Administrative distance: 110
            External admin-distance: 110
            Inter-area admin-distance: 110
            Intra-area admin-distance: 110
   Originating router-LSAs with maximum metric:
        Administrative: active
          Advertise stub links with maximum metric in router-LSAs
          Advertise external-LSAs with metric 55555
        On-Startup: interval for 900 second, state: inactive
          Advertise stub links with maximum metric in router-LSAs
          Advertise external-LSAs with metric 33333
   Number of external LSA 10. Checksum Sum 0x0fb29537
   Number of areas in this router is 1
   All adjacency changes are logged

   Area ID: 0.0.0.0 (Backbone)
          Number of interfaces in this area: Total: 4, Active: 4
          Number of fully adjacent neighbors in this area: 3
          Area has no authentication
          SPF algorithm executed 15 times
          MPLS TE Admin state: Enabled
          Number of LSA 30
          Number of router LSA 9. Checksum Sum 0x000484a0
          Number of network LSA 0. Checksum Sum 0x00000000
          Number of summary LSA 0. Checksum Sum 0x00000000
          Number of ASBR summary LSA 0. Checksum Sum 0x00000000
          Number of NSSA LSA 0. Checksum Sum 0x00000000
          Number of opaque link LSA 0. Checksum Sum 0x00000000
          Number of opaque area LSA 21. Checksum Sum 0x000ac851
          BFD: Admin state:Enabled
                Minimum Tx Interval: 150
                Minimum Rx Interval: 150
                BFD multiplier: 3


  dnRouter#show ospfv3

   OSPFv3 Routing Process (0) with Router-ID 1.1.1.1
   Running 00:14:33
   Initial SPF scheduling delay 50 millisec(s)
   Minimum hold time between consecutive SPFs 200 millisec(s)
   Maximum hold time between consecutive SPFs 5000 millisec(s)
   Hold time multiplier is currently 1
   SPF algorithm last executed 00:14:28 ago
   Last SPF duration 0 sec 1419 usec
   SPF timer is inactive
   Initial LSA scheduling delay 50 millisec(s)
   Minimum hold time between consecutive LSA generation 200 millisec(s)
   Maximum hold time between consecutive LSA generation 5000 millisec(s)
   Refresh timer 1800 secs
   Maximum ECMP paths 32
   Auto-Cost reference-bandwidth: 100mbps
   Graceful-Restart:
        Restarting-mode:
          Admin state: enabled
          Grace period: 120 secs
          Grace interval: 60 secs
        Helper-mode:
          Admin state: disabled
   Number of AS scoped LSAs is 0
          Administrative distance: 110
            External admin-distance: 110
            Inter-area admin-distance: 110
            Intra-area admin-distance: 110
   Originating router-LSAs with maximum metric:
        Administrative: inactive
        On-Startup: interval for 1200 second, state: active, 2m16s remaining
          Advertise stub links with maximum metric in router-LSAs
          Advertise external-LSAs with metric 33333
   Number of external LSA 10. Checksum Sum 0x0fbc2637
   Number of areas in this router is 1
   All adjacency changes are logged

   Area ID: 0.0.0.0 (Backbone)
          Number of interfaces in this area: Total: 4, Active: 4
          Number of fully adjacent neighbors in this area: 3
          Area has no authentication
          SPF algorithm executed 15 times
          MPLS TE Admin state: Enabled
          Number of LSA 30
          Number of router LSA 9. Checksum Sum 0x000484a0
          Number of network LSA 0. Checksum Sum 0x00000000
          Number of summary LSA 0. Checksum Sum 0x00000000
          Number of ASBR summary LSA 0. Checksum Sum 0x00000000
          Number of NSSA LSA 0. Checksum Sum 0x00000000
          Number of opaque link LSA 0. Checksum Sum 0x00000000
          Number of opaque area LSA 21. Checksum Sum 0x000ac851
          BFD: Admin state:Enabled
                Minimum Tx Interval: 50
                Minimum Rx Interval: 50
                BFD multiplier: 5

.. **Help line:** Displays OSPFv3 information

**Command History**

+---------+--------------------------------------------------------------------------------------+
| Release | Modification                                                                         |
+=========+======================================================================================+
| 11.6    | Command introduced                                                                   |
+---------+--------------------------------------------------------------------------------------+
| 15.0    | Updated show output with max-metric remaining timer from area level to general level |
+---------+--------------------------------------------------------------------------------------+
