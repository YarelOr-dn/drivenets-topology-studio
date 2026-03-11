show segment-routing policy
---------------------------

**Minimum user role:** viewer

To display segment-routing policy information:

**Command syntax: show segment-routing policy** {state [state] origin [origin] destination [destination-address] color [color] detail \| name [policy-name}

**Command mode:** operational

**Parameter table**

+---------------------+---------------------------------------------------------------------------+
| Parameter           | Description                                                               |
+=====================+===========================================================================+
| policy-name         | Displays detailed information for a specific policy matching policy name. |
+---------------------+---------------------------------------------------------------------------+
| detail              | Displays detailed information for all SR-TE policies.                     |
+---------------------+---------------------------------------------------------------------------+
| state               | Filters output per SR-TE policy state.                                    |
+---------------------+---------------------------------------------------------------------------+
| origin              | Filters output per SR-TE policy origin.                                   |
+---------------------+---------------------------------------------------------------------------+
| destination-address | Filters output per SR-TE policy destination IP address.                   |
+---------------------+---------------------------------------------------------------------------+
| color               | Filters output per SR-TE policy color.                                    |
+---------------------+---------------------------------------------------------------------------+

**Example**
::

  dnRouter# show segment-routing policy

  Destination     Color      Origin       State       TX[Mbps]            Active-Path       Backup-Path          Name
  ------------------------------------------------------------------------------------------------------------------------------------
  100.0.0.2       0          Static       up          3291.02             PATH_1            -                    SR_POL_P1_P2
  100.0.0.3       0          Static       up          18.41               -                 -                    SR_POL_P1_P3
  100.0.0.4       0          Static       down        0                   PATH_3            -                    SR_POL_P1_P4
  4.4.4.4         0          PCE          up          0                   pol4              -                    pol4
  5.5.5.5         0          Auto         up          0                                     -                    Auto_c_0_dest_5.5.5.5
  6.6.6.6         0          Auto         up          0                                     -                    Auto_c_0_dest_6.6.6.6
  8.8.8.8         5          Static       up          0                   path2             path4                pol1


  dnRouter# show segment-routing policy name SR_POL_P1_P2

  SR-TE policy: SR_POL_P1_P2
          State: up
          Destination: 100.0.0.2
          Local-ID: 524289
          Source: 100.0.0.1
          Description: "uncolored policy to P2 load-balance traffic over 2 unequal paths"
          Color: 0
          Administrative-distance: 103
          Origin: Static
          IGP metric: 301
          Local mpls-forwarding label: 10002
          Reoptimization: enabled, interval: 300s, next: due-in 157s
          Active-Path: PATH_1, id: 1, priority: 2
            Lock remaining: 0s
            segment-list 1 weight 1
              hop 1 include prefix-sid ipv4-address 9.9.9.9 strict-spf
            segment-list 2 weight 1
              hop 1 include prefix-sid ipv4-address 11.11.11.11 strict-spf
              hop 2 include prefix-sid ipv4-address 5.5.5.5 strict-spf
            Egress label stack:
              Protocol ISIS INST_1 level-2
              segment-list 1: 11009, 11002 via bundle-1
                alternate: 11009, 11002 via bundle-10
              segment-list 2: 11011, 11005, 11002 via bundle-2
          Backup-Path: N/A
          IGP-Shortcuts enabled
          Seamless BFD:
            Admin State: disabled
          Destination-RIB: both
          Pending-Paths: N/A
          Validation:
            PATH_1 (prio: 2), State: Success, Last Validation: 14-Jul-2023-07:34:52
          PCE Delegation: disabled
  
          Policy discriminators:
              binding-sid: 524289
              Path id: 1, name: PATH_1 sbfd initiator discriminator: 1608

          Policy statistics:
              Packets: 101,489,552,909,102 (3291.02 Mbps)
              Bytes: 129,654,704,749 (1 Mpps)


  dnRouter# show segment-routing policy name SR_POL_P1_P4

  SR-TE policy: SR_POL_P1_P4
      State: invalid
      Destination: 100.0.0.4
      Source: 100.0.0.1
      Description: "uncolored policy to P4 load-balance traffic over 2 unequal paths"
      Color: 0
      Administrative-distance: 103
      Origin: Static
      Retry: 25s
      IGP-Shortcuts disabled
      Seamless BFD:
        Admin State: disabled
      Destination-RIB: mpls-forwarding
      Validation:
        PATH_3 (prio: 1), State: Error (unable to resolve hop 1 for segment-list 1), Last Validation: 14-Jul-2023-08:05:34
      PCE Delegation: disabled

      Policy discriminators:
          binding-sid: 524289
          Path id: 1, name: PATH_3 no sbfd initiator discriminator

      Policy statistics:
        Packets: 101,489 (0 Mbps)
        Bytes: 129,654 (0 Mpps)


  dnRouter# show segment-routing policy name pol4

  SR-TE policy: pol4
      State: up
      Destination: 4.4.4.4 spf
      Local-ID: 8006
      Binding-SID: 8006
      Color: 0
      Administrative-distance: 103
      Origin: PCE
      IGP metric: 20
      Local mpls-forwarding label: 16004
      Active-Path: <pce-path>, priority: 256
        Lock remaining: 0s
        Egress label stack:
          Protocol ISIS one level-2
          segment-list 1:
            3, 16003, 16004, via vdev_12
      Backup-Path: N/A
      IGP-Shortcut: disabled
      LDP tunneling: disabled, LDP-sync: disabled, LDP status: down
      Seamless BFD:
          Admin State: disabled
      Destination-RIB: mpls-forwarding
      Policy statistics:
        Packets: 101,489 (0 Mbps)
        Bytes: 129,654 (0 Mpps)
      Pending-Paths: N/A
      Validation:
          <pce-path> (prio: 256), State: Success, Last Validation: 20-Apr-2023-13:58:42
      PCE Delegation: enabled
        Last received ERO: Thu Apr 20 13:58:42 2023
        Path: pcep: <pol4>, Priority: 0
          SID[0]: Label: 16002, NAI: 2.2.2.2/32
          SID[1]: Label: 16003, NAI: 3.3.3.3/32

  dnRouter# show segment-routing policy name pol1

  SR-TE policy: pol1
      State: up
      Destination: 8.8.8.8 spf
      Source: 1.1.1.1
      Local-ID: 8002
      Binding-Sid: 8002
      Color: 5
      Administrative-distance: 103
      Origin: Static
      IGP metric: 41
      Local mpls-forwarding label: N/A
      Reoptimization: enabled, interval: 1, next: due-in 0s
      Active-Path: path2, id: 3, priority: 4
          Lock remaining: 0s
          segment-list 2 weight 1
              hop 10 prefix 3.3.3.3/32 spf
          Egress label stack:
              Protocol OSPF ospf-1, VRF default, area 0.0.0.0
              segment-list 2:
                  16003, 16008, via vdev_12
      Backup-Path: path4, id: 5, priority: 2
          segment-list 2 weight 1
              hop 10 prefix 6.6.6.6/32 spf
          Egress label stack:
              Protocol OSPF ospf-1, VRF default, area 0.0.0.0
              segment-list 2:
                  16006, 16008, via vdev_12
                  16006, 16008, via vdev_15
      IGP-Shortcut: disabled
      No fallback: disabled
      Ldp tunneling: disabled, Ldp-Sync: disabled, Ldp status: down
      Seamless BFD:
          Admin State: disabled
      Destination-Rib: mpls-forwarding
      Pending-Paths: N/A
      Validation:
          path1 (prio: 5), State: Error (No route to first hop. Cannot resolve destination hop label), Last Validation: 14-Jul-2023-09:24:28
          path2 (prio: 4), State: Success, Last Validation: 14-Jul-2023-09:24:28
          path3 (prio: 3), State: Error (Same node for consecutive hops, RID=4.4.4.4, hop=10), Last Validation: 14-Jul-2023-09:24:28
          path4 (prio: 2), State: Success, Last Validation: 14-Jul-2023-09:24:28
          path5 (prio: 1), State: Unvalidated
      PCE Delegation: disabled

      Policy discriminators:
          binding-sid: 8002
          Path id: 3, name: path2 no sbfd initiator discriminator
          Path id: 5, name: path4 no sbfd initiator discriminator

      Policy statistics:
        Packets: 101,489 (0 Mbps)
        Bytes: 129,654 (0 Mpps)


  dnRouter# show segment-routing policy name pol1

  SR-TE policy: pol1
      State: installed
      Destination: 8.8.8.8 spf
      Source: 1.1.1.1
      Local-ID: 8002
      Binding-Sid: 8002
      Color: 0
      Administrative-distance: 103
      Origin: Static
      Reoptimization: enabled, interval: 3, next: due-in 2s
      Active-Path: N/A
      Backup-Path: N/A
      IGP-Shortcut: disabled
      No fallback: disabled
      Ldp tunneling: disabled, Ldp-Sync: disabled, Ldp status: down
      Seamless BFD:
          Admin State: enabled
          Remote Reflector: 100 Source: Policy configuration
          Failure Action: down
          Transmit Interval: 300 ms, Multiplier: 3
      Destination-Rib: mpls-forwarding
      Pending-Path: via3, id: 2, priority: 20
          Pending Reason: S-BFD
          segment-list 2 weight 1
              hop 10 prefix 3.3.3.3/32 spf
          Egress label stack:
              Protocol OSPF ospf-1, VRF default, area 0.0.0.0
              segment-list 2:
                  16003, 16008, via vdev_12
      Pending-Path: via2via6, id: 1, priority: 10
          Pending Reason: S-BFD
          segment-list 2 weight 1
              hop 10 prefix 2.2.2.2/32 spf
              hop 20 prefix 6.6.6.6/32 spf
          Egress label stack:
              Protocol OSPF ospf-1, VRF default, area 0.0.0.0
              segment-list 2:
                  3, 16006, 16008, via vdev_12
      Validation:
          via3 (prio: 20), State: Success, Last Validation: 14-Jul-2023-09:48:34
          via2via6 (prio: 10), State: Success, Last Validation: 14-Jul-2023-09:48:34
      PCE Delegation: disabled

      Policy discriminators:
          binding-sid: 8002
          Path id: 2, name: via3 sbfd initiator discriminator: 1608
          Path id: 1, name: via2via6 sbfd initiator discriminator: 1612

      Policy statistics:
        Packets: 101,489 (0 Mbps)
        Bytes: 129,654 (0 Mpps)


        dnRouter# show segment-routing policy name Auto_c_0_dest_5.5.5.5

        SR-TE policy: Auto_c_0_dest_5.5.5.5
          State: up
          Destination: 5.5.5.5 spf
          Local-ID: 8006
          Binding-SID: 8006
          Color: 0
          Administrative-distance: 103
          Origin: Auto
          IGP metric: 20
          Local MPLS-forwarding label: 16004
          Egress label stack:
            Protocol ISIS one level-2
            segment-list 1:
              3, 16003, 16004, via vdev_12
          IGP-Shortcut: disabled
          LDP tunneling: disabled, LDP-sync: disabled, LDP status: down
          Destination-RIB: MPLS-forwarding
          Policy statistics:
	    Packets: 101,489 (0 Mbps)
	    Bytes: 129,654 (0 Mpps)
          Validation: Success
            Last Error: N/A
          auto-policy: created for 4 services (BGP)


        dnRouter# show segment-routing policy name Auto_c_0_dest_6.6.6.6

        SR-TE policy: Auto_c_0_dest_6.6.6.6
          State: up
          Destination: 6.6.6.6 spf
          Local-ID: 8006
          Binding-SID: 8006
          Color: 0
          Administrative-distance: 103
          Origin: Auto
          IGP metric: 20
          Local MPLS-forwarding label: 16004
          Egress label stack:
            Protocol ISIS one level-2
            segment-list 1:
              3, 16003, 16004, via vdev_12
          IGP-Shortcut: disabled
          LDP tunneling: disabled, LDP-sync: disabled, LDP status: down
          Destination-RIB: MPLS-forwarding
          Policy statistics:
            Packets: 101,489 (0 Mbps)
            Bytes: 129,654 (0 Mpps)
          Validation: Success
            Last Error: N/A
          auto-policy: created for 0 services (BGP), pending remove in 28 sec

  dnRouter# show segment-routing policy name S_SPF_C_0

  SR-TE policy: S_SPF_C_0
    State: up
    Destination: 4.4.4.4 strict-spf
    Source: 1.1.1.1
    Local-ID: 260
    Binding-Sid: 260 (dynamic)
    Color: 0
    Administrative-distance: 103
    Origin: Static
    IGP metric: 21
    Local mpls-forwarding label: N/A 
    Active-Path: internal-empty-path-internal, id: 1, priority: 0
        Lock remaining: 0s
        segment-list 2 weight 1
        Egress label stack:
            Protocol OSPF, area 0.0.0.0
            segment-list 2:
                16204, via vdev_13
    Backup-Path: backup-path-install unset
    IGP-Shortcut: disabled
    No fallback: disabled
    Ldp tunneling: disabled, Ldp-Sync: disabled, Ldp status: down
    Seamless BFD:
        Admin State: disabled
    Destination-Rib: mpls-forwarding
    Pending-Paths: N/A
    Validation: 
        internal-empty-path-internal (prio: 0, static-sl), State: Success, Last Validation: 16-Feb-2024-10:54:25
    PCE Delegation: No update received from PCE

  dnRouter# show segment-routing policy name S_SPF_C_100

  SR-TE policy: S_SPF_C_0
    State: up
    Destination: 4.4.4.4 strict-spf
    Source: 1.1.1.1
    Local-ID: 260
    Binding-Sid: 260 (dynamic)
    Color: 100
    Administrative-distance: 103
    Origin: Static
    IGP metric: 21
    Local mpls-forwarding label: N/A 
    Active-Path: internal-empty-path-internal, id: 1, priority: 0
        Lock remaining: 0s
        segment-list 2 weight 1
        Egress label stack:
            Protocol OSPF, area 0.0.0.0
            segment-list 2:
                16204, via vdev_13
    Backup-Path: backup-path-install unset
    IGP-Shortcut: disabled
    No fallback: disabled
    Ldp tunneling: disabled, Ldp-Sync: disabled, Ldp status: down
    Seamless BFD:
        Admin State: disabled
    Destination-Rib: mpls-forwarding
    Pending-Paths: N/A
    Validation: 
        internal-empty-path-internal (prio: 0, static-sl), State: Success, Last Validation: 16-Feb-2024-10:54:25
    PCE Delegation: No update received from PCE

.. **Help line:** Displays segment-routing policy information

**Command History**

+---------+-----------------------------------------------------------------------------------------------+
| Release | Modification                                                                                  |
+=========+===============================================================================================+
| 15.0    | Command introduced                                                                            |
+---------+-----------------------------------------------------------------------------------------------+
| 18.2    | Added filters, renamed Local/PCE field to Origin, and added support for PCE and auto-policies |
+---------+-----------------------------------------------------------------------------------------------+
| 18.3    | Added sbfd info, backup, pending paths, validation timestamps                                 |
+---------+-----------------------------------------------------------------------------------------------+
| 19.1    | Display "N/A" for "Local mpls-forwarding label" for policies that are not ILM overrides.      |
+---------+-----------------------------------------------------------------------------------------------+
