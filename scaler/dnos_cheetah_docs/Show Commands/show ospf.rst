show ospf
----------

**Minimum user role:** viewer

The show ospf command displays information on a variety of general OSPF and OSPFv3 configuration information. You can filter the information by parameter and/or by interface name. When filtering by parameter only, the system displays the requested parameter for all interfaces. When filtering by interface name, the information is further filtered to display the parameter configuration for the requested interface only.

**Command syntax: show ospf** instance [ospf-instance-name]

**Command mode:** operational


..
	**Internal Note**

	- use "instance [ospf-instance-name]" to display information from a specific OSPF instance, when not specified, display information from all OSPF instances

**Parameter table**

The following are the parameters whose value you can display for a specific interface or for all interfaces:

+--------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                                           |
+====================+=======================================================================================================================================+
| border-router      | Displays OSPF information for an area. See show ospf border-router.                                                                   |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| route              | Displays the OSPF routing table, as determined by the most recent SPF calculation. See show ospf route.                               |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| neighbor           | Displays information on OSPF neighbors (all or filtered by interface). See show ospf neighbors and show ospf neighbors detail.        |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| interface          | Displays concentric information on the OSPF process on all OSPF-enabled interfaces or on a named interface. See show ospf interfaces. |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| database           | Display lists of information related to the OSPF database. See .                                                                      |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| ospf-instance-name | Filters the displayed information to a specific OSPF instance.                                                                        |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

      dnRouter# show ospf

      Maximum routes limit 32000 threshold 75%
      Maximum adjacencies 500 warning threshold 75%
      OSPF Instance instance1:
        OSPF Routing Process, Router ID: 100.11.11.11
        OSPF TE Router ID: 100.11.11.11
        Supports only single TOS (TOS0) routes
        This implementation conforms to RFC2328
        RFC1583 Compatibility flag is disabled
        OpaqueCapability flag is enabled
        Originating LSAs with maximum metric:
          Administrative: active
            Advertise router-LSA PTP links with maximum metric
            Advertise router-LSA stub links with maximum metric
            Advertise external-LSAs with metric 500
            Advertise opaque-area-LSAs with TE metric 65535
            Advertise opaque-area-LSAs with maximum delay metrics
          On-Startup: interval 300 seconds, state: inactive
            Advertise router-LSA PTP links with maximum metric
            Advertise router-LSA stub links with maximum metric
            Advertise external-LSAs with metric 400
            Advertise opaque-area-LSAs with TE metric 65535
            Advertise opaque-area-LSAs with maximum delay metrics
        SPF Scheduling:
          Initial SPF scheduling delay 200 millisec(s)
          Minimum hold time between consecutive SPFs 1000 millisec(s)
          Maximum hold time between consecutive SPFs 10000 millisec(s)
          Hold time multiplier is currently 4
          SPF algorithm last executed 12m17s ago
          Last SPF duration 0.001s
          SPF timer is inactive
        LSA Scheduling:
          Initial LSA scheduling delay 50 millisec(s)
          Minimum hold time between consecutive LSA generation 200 millisec(s)
          Maximum hold time between consecutive LSA generation 5000 millisec(s)
        Refresh timer 1800 secs
        This router is an ASBR (injecting external routing information)
        Redistributing external routes from: static
          maximum number of redistributed prefixes 1000 warning threshold 80%
        Maximum ECMP paths 32
        Auto-Cost reference-bandwidth: 4294967mbps
        Administrative distance: 110
          External admin-distance: 110
          Inter-area admin-distance: 110
          Intra-area admin-distance: 110
        LDP sync is disabled
        Segment-Routing MPLS: enabled
          SRGB: 16000-23999
          SRLB: 8000-15999
        Fast-reroute backup-candidate: enabled
        Graceful-restart:
          Restarting-mode:
            Admin-state: enabled
            Grace-period: 120 secs
            Grace-interval: 60 secs
          Helper-mode:
            IETF mode: enabled
            Cisco mode : enabled
        Number of external LSA 8002. Checksum Sum 0x0fb29537
        Number of opaque AS LSA 0. Checksum Sum 0x00000000
        Number of areas attached to this router: 1
        Adjacency changes are logged

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
                RSVP dependency: disabled
          TI-LFA: enabled, node-protection, maximum-labels 3, strict-spf-protection
          Microloop avoidance is enabled, maximum-labels: 3, fib-delay: 15000 ms


      dnRouter# show ospf instance instance1

      Maximum routes limit 32000 threshold 75%
      Maximum adjacencies 500 warning threshold 75%
      OSPF Instance instance1:
        OSPF Routing Process, Router ID: 100.11.11.11
        OSPF TE Router ID: 100.11.11.11
        Supports only single TOS (TOS0) routes
        This implementation conforms to RFC2328
        RFC1583 Compatibility flag is disabled
        OpaqueCapability flag is enabled
        Originating LSAs with maximum metric, Time remaining: 4m57s:
          On-Startup: interval 300 seconds, state: active
            Advertise router-LSA PTP links with maximum metric
            Advertise router-LSA stub links with maximum metric
            Advertise external-LSAs with metric 400
            Advertise opaque-area-LSAs with TE metric 65535
            Advertise opaque-area-LSAs with maximum delay metrics
        SPF Scheduling:
          Initial SPF scheduling delay 200 millisec(s)
          Minimum hold time between consecutive SPFs 1000 millisec(s)
          Maximum hold time between consecutive SPFs 10000 millisec(s)
          Hold time multiplier is currently 4
          SPF algorithm last executed 12m17s ago
          Last SPF duration 0.001s
          SPF timer is inactive
        LSA Scheduling:
          Initial LSA scheduling delay 50 millisec(s)
          Minimum hold time between consecutive LSA generation 200 millisec(s)
          Maximum hold time between consecutive LSA generation 5000 millisec(s)
        Refresh timer 1800 secs
        This router is an ASBR (injecting external routing information)
        Redistributing external routes from: static
          maximum number of redistributed prefixes 1000 warning threshold 80%
        Maximum ECMP paths 32
        Auto-Cost reference-bandwidth: 4294967mbps
        Administrative distance: 110
          External admin-distance: 110
          Inter-area admin-distance: 110
          Intra-area admin-distance: 110
        LDP sync is disabled
        Segment-Routing MPLS: enabled
          SRGB: 16000-23999
          SRLB: 8000-15999
        Fast-reroute backup-candidate: enabled
        Graceful-restart:
          Restarting-mode:
            Admin-state: enabled
            Grace-period: 120 secs
            Grace-interval: 60 secs
          Helper-mode:
            IETF mode: enabled
            Cisco mode : enabled
        Number of external LSA 8002. Checksum Sum 0x0fb29537
        Number of opaque AS LSA 0. Checksum Sum 0x00000000
        Number of areas attached to this router: 1
        Adjacency changes are logged

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
                RSVP dependency: disabled
          TI-LFA: enabled, node-protection, maximum-labels 3, strict-spf-protection
          Microloop avoidance is enabled, maximum-labels: 3, fib-delay: 15000 ms
                SPF: 13461 ms remaining
                Flex-Algorithm 130: 13474 ms remaining


      dnRouter# show ospf

      Maximum routes limit 32000 threshold 75%
      Maximum adjacencies 500 warning threshold 75%
      OSPF Instance instance1:
        OSPF Routing Process, Router ID: 99.99.2.100
            Domain-tag: disabled
        OSPF TE Router ID: 2.3.1.2
        Supports only single TOS (TOS0) routes
        This implementation conforms to RFC2328
        RFC1583 Compatibility flag is disabled
        OpaqueCapability flag is enabled
        SPF Scheduling:
          Initial SPF scheduling delay 50 millisec(s)
          Minimum hold time between consecutive SPFs 200 millisec(s)
          Maximum hold time between consecutive SPFs 5000 millisec(s)
          Hold time multiplier is currently 1
          SPF algorithm last executed 4m23s ago
          Last SPF duration 0.002s
          SPF timer is inactive
        LSA Scheduling:
          Initial LSA scheduling delay 500 millisec(s)
          Minimum hold time between consecutive LSA generation 5000 millisec(s)
          Maximum hold time between consecutive LSA generation 5000 millisec(s)
        Refresh timer 1800 secs
        Area Border Router
        Maximum ECMP paths 16
        Auto-Cost reference-bandwidth: 100mbps
        Administrative distance: 110
          External admin-distance: 110
          Inter-area admin-distance: 110
          Intra-area admin-distance: 110
        LDP sync is disabled
        Segment-Routing MPLS: enabled
          SRGB: 16000-23999
          SRLB: 8000-15999
        Fast-reroute backup-candidate: enabled
        Graceful-restart:
          Restarting-mode:
            Admin-state: enabled
            Grace-period: 120 secs
            Grace-interval: 60 secs
          Helper-mode:
            IETF mode: enabled
            Cisco mode : enabled
        Number of external LSA 0. Checksum Sum 0x00000000
        Number of opaque AS LSA 0. Checksum Sum 0x00000000
        Number of areas attached to this router: 2

        Area ID: 0.0.0.0 (Backbone)
          Number of interfaces in this area: Total: 1, Active: 1
          Number of fully adjacent neighbors in this area: 1
          Area has no authentication
          SPF algorithm executed 5 times
          MPLS TE Admin state: Disabled
          Number of LSA 4
          Number of router LSA 2. Checksum Sum 0x0001d84d
          Number of network LSA 0. Checksum Sum 0x00000000
          Number of summary LSA 2. Checksum Sum 0x0001023c
          Number of ASBR summary LSA 0. Checksum Sum 0x00000000
          Number of NSSA LSA 0. Checksum Sum 0x00000000
          Number of opaque link LSA 0. Checksum Sum 0x00000000
          Number of opaque area LSA 0. Checksum Sum 0x00000000
          BFD: Admin state:Disabled
                Minimum Tx Interval: 300
                Minimum Rx Interval: 300
                BFD multiplier: 3
                RSVP dependency: disabled
          OSPF TI-LFA is not enabled
          Microloop avoidance is not enabled

        Area ID: 0.0.0.1 (Stub)
          Shortcutting mode: Default, S-bit consensus: no
          Number of interfaces in this area: Total: 1, Active: 1
          Number of fully adjacent neighbors in this area: 1
          Area has no authentication
          Number of full virtual adjacencies going through this area: 0
          SPF algorithm executed 11 times
          MPLS TE Admin state: Disabled
          Number of LSA 4
          Number of router LSA 2. Checksum Sum 0x000175ba
          Number of network LSA 0. Checksum Sum 0x00000000
          Number of summary LSA 2. Checksum Sum 0x0001163a
          Number of ASBR summary LSA 0. Checksum Sum 0x00000000
          Number of NSSA LSA 0. Checksum Sum 0x00000000
          Number of opaque link LSA 0. Checksum Sum 0x00000000
          Number of opaque area LSA 0. Checksum Sum 0x00000000
          BFD: Admin state:Disabled
                Minimum Tx Interval: 300
                Minimum Rx Interval: 300
                BFD multiplier: 3
                RSVP dependency: disabled
          OSPF TI-LFA is not enabled
          Microloop avoidance is not enabled

        Area ID: 0.0.0.2 (NSSA, no summary)
          Shortcutting mode: Default, S-bit consensus: ok
          Number of interfaces in this area: Total: 1, Active: 1
          Elected NSSA/ABR performs type-7/type-5 LSA translation.
          We are an ABR and the NSSA Elected Translator.
          Number of fully adjacent neighbors in this area: 0
          Area has no authentication
          Number of full virtual adjacencies going through this area: 0
          SPF algorithm executed 13 times
          MPLS TE Admin state: Disabled
          Number of LSA 4
          Number of router LSA 2. Checksum Sum 0x000165f5
          Number of network LSA 0. Checksum Sum 0x00000000
          Number of summary LSA 1. Checksum Sum 0x0000849b
          Number of ASBR summary LSA 0. Checksum Sum 0x00000000
          Number of NSSA LSA 1. Checksum Sum 0x000093a9
          Number of opaque link LSA 0. Checksum Sum 0x00000000
          Number of opaque area LSA 0. Checksum Sum 0x00000000
          BFD: Admin state:Disabled
                Minimum Tx Interval: 300
                Minimum Rx Interval: 300
                BFD multiplier: 3
                RSVP dependency: disabled
          OSPF TI-LFA is not enabled
          Microloop avoidance is not enabled

      dnRouter# show ospf instance instance1

      Maximum routes limit 32000 threshold 75%
      Maximum adjacencies 500 warning threshold 75%
      OSPF Instance instance1:
        OSPF Routing Process, Router ID: 99.99.2.100
            Domain-tag: disabled
        OSPF TE Router ID: 2.3.1.2
        Supports only single TOS (TOS0) routes
        This implementation conforms to RFC2328
        RFC1583 Compatibility flag is disabled
        OpaqueCapability flag is enabled
        SPF Scheduling:
          Initial SPF scheduling delay 50 millisec(s)
          Minimum hold time between consecutive SPFs 200 millisec(s)
          Maximum hold time between consecutive SPFs 5000 millisec(s)
          Hold time multiplier is currently 1
          SPF algorithm last executed 4m23s ago
          Last SPF duration 0.002s
          SPF timer is inactive
        LSA Scheduling:
          Initial LSA scheduling delay 500 millisec(s)
          Minimum hold time between consecutive LSA generation 5000 millisec(s)
          Maximum hold time between consecutive LSA generation 5000 millisec(s)
        Refresh timer 1800 secs
        Area Border Router
        Maximum ECMP paths 16
        Auto-Cost reference-bandwidth: 100mbps
        Administrative distance: 110
          External admin-distance: 110
          Inter-area admin-distance: 110
          Intra-area admin-distance: 110
        LDP sync is disabled
        Segment-Routing MPLS: enabled
          SRGB: 16000-23999
          SRLB: 8000-15999
        Fast-reroute backup-candidate: enabled
        Graceful-restart:
          Restarting-mode:
            Admin-state: enabled
            Grace-period: 120 secs
            Grace-interval: 60 secs
          Helper-mode:
            IETF mode: enabled
            Cisco mode : enabled
        Number of external LSA 0. Checksum Sum 0x00000000
        Number of opaque AS LSA 0. Checksum Sum 0x00000000
        Number of areas attached to this router: 2

        Area ID: 0.0.0.0 (Backbone)
          Number of interfaces in this area: Total: 1, Active: 1
          Number of fully adjacent neighbors in this area: 1
          Area has no authentication
          SPF algorithm executed 5 times
          MPLS TE Admin state: Disabled
          Number of LSA 4
          Number of router LSA 2. Checksum Sum 0x0001d84d
          Number of network LSA 0. Checksum Sum 0x00000000
          Number of summary LSA 2. Checksum Sum 0x0001023c
          Number of ASBR summary LSA 0. Checksum Sum 0x00000000
          Number of NSSA LSA 0. Checksum Sum 0x00000000
          Number of opaque link LSA 0. Checksum Sum 0x00000000
          Number of opaque area LSA 0. Checksum Sum 0x00000000
          BFD: Admin state:Disabled
                Minimum Tx Interval: 300
                Minimum Rx Interval: 300
                BFD multiplier: 3
                RSVP dependency: disabled
          OSPF TI-LFA is not enabled
          Microloop avoidance is not enabled

        Area ID: 0.0.0.1 (Stub)
          Shortcutting mode: Default, S-bit consensus: no
          Number of interfaces in this area: Total: 1, Active: 1
          Number of fully adjacent neighbors in this area: 1
          Area has no authentication
          Number of full virtual adjacencies going through this area: 0
          SPF algorithm executed 11 times
          MPLS TE Admin state: Disabled
          Number of LSA 4
          Number of router LSA 2. Checksum Sum 0x000175ba
          Number of network LSA 0. Checksum Sum 0x00000000
          Number of summary LSA 2. Checksum Sum 0x0001163a
          Number of ASBR summary LSA 0. Checksum Sum 0x00000000
          Number of NSSA LSA 0. Checksum Sum 0x00000000
          Number of opaque link LSA 0. Checksum Sum 0x00000000
          Number of opaque area LSA 0. Checksum Sum 0x00000000
          BFD: Admin state:Disabled
                Minimum Tx Interval: 300
                Minimum Rx Interval: 300
                BFD multiplier: 3
                RSVP dependency: disabled
          OSPF TI-LFA is not enabled
          Microloop avoidance is not enabled

        Area ID: 0.0.0.2 (NSSA, no summary)
          Shortcutting mode: Default, S-bit consensus: ok
          Number of interfaces in this area: Total: 1, Active: 1
          Elected NSSA/ABR performs type-7/type-5 LSA translation.
          We are an ABR and the NSSA Elected Translator.
          Number of fully adjacent neighbors in this area: 0
          Area has no authentication
          Number of full virtual adjacencies going through this area: 0
          SPF algorithm executed 13 times
          MPLS TE Admin state: Disabled
          Number of LSA 4
          Number of router LSA 2. Checksum Sum 0x000165f5
          Number of network LSA 0. Checksum Sum 0x00000000
          Number of summary LSA 1. Checksum Sum 0x0000849b
          Number of ASBR summary LSA 0. Checksum Sum 0x00000000
          Number of NSSA LSA 1. Checksum Sum 0x000093a9
          Number of opaque link LSA 0. Checksum Sum 0x00000000
          Number of opaque area LSA 0. Checksum Sum 0x00000000
          BFD: Admin state:Disabled
                Minimum Tx Interval: 300
                Minimum Rx Interval: 300
                BFD multiplier: 3
                RSVP dependency: disabled
          Segment-Routing is disabled
          OSPF TI-LFA is not enabled
          Microloop avoidance is not enabled

.. **Help line:** Displays OSPF information

**Command History**

+---------+--------------------------------------------------------------------------------------+
| Release | Modification                                                                         |
+=========+======================================================================================+
| 11.6    | Command introduced                                                                   |
+---------+--------------------------------------------------------------------------------------+
| 15.0    | Updated show output with max-metric remaining timer from area level to general level |
+---------+--------------------------------------------------------------------------------------+
| 18.2    | Added instance parameter                                                             |
+---------+--------------------------------------------------------------------------------------+
| 18.2    | Added Stub/NSSA areas                                                                |
+---------+--------------------------------------------------------------------------------------+
| 18.2    | Added Microloop avoidance                                                            |
+---------+--------------------------------------------------------------------------------------+
| 19.0    | Updated show output for max-metric and also included metric types                    |
+---------+--------------------------------------------------------------------------------------+
