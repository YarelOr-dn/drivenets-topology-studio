show vpws detail
----------------

**Minimum user role:** viewer

Display the detailed VPWS service status for all VPWS instances. You can filter the output for specific instances using the command parameters:

The information displayed enables you to monitor the VPWS status of the Pseudowire state. This hardcoded feature is always enabled. The VPWS status messages are only displayed if both sides have VPWS status enabled. The status codes are:

0x00000000 - Pseudowire forwarding (clear all failures)

0x00000001 - Pseudowire not forwarding

0x00000002 - Local Attachment Circuit (ingress) receive fault

0x00000004 - Local Attachment Circuit (egress) transmit fault

0x00000008 - Local PSN-facing PW (ingress) receive fault

0x00000010 - Local PSN-facing PW (egress) transmit fault

**Command syntax: show vpws detail** instance [instance-name] interface [interface-name] neighbor [ipv4-address] pw-id [pw-id] state [state]

**Command mode:** operational

**Note**

- When applying multiple filters the output is the combination of all filters.

**Parameter table**

+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| Parameter      | Description                                             | Range                                                                                                                                                                                                                                                         | Default |
+================+=========================================================+===============================================================================================================================================================================================================================================================+=========+
| instance-name  | The configured VPWS instance name.                      | string 1..255                                                                                                                                                                                                                                                 | \-      |
+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| interface-name | The local interface name.                               | string 1..255                                                                                                                                                                                                                                                 | \-      |
+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| ipv4-address   | The neighbors IP address.                               | A.B.C.D                                                                                                                                                                                                                                                       | \-      |
+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| pw-id          | The configured PW-ID.                                   | 1..4294967295                                                                                                                                                                                                                                                 | \-      |
+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| state          | The VPWS state. If Down, the down reason is displayed.  | Up, Down, Admin-down.                                                                                                                                                                                                                                         | \-      |
|                |                                                         | Down reasons: local-not-ready, control-word-mismatch ,remote-PSN-port-failure, mtu-mismatch, encap-mismatch, no-mpls-reachability, no-local-AC, local-AC-down, remote-not-ready, remote-AC-down, no-local-AC, local-AC-down, remote-not-ready, remote-AC-down |         |
+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+

**Example**
::

    dnRouter# show vpws detail

    VPWS: R15_R16_0
    Admin state: enabled, Operational state: up, Time in state: 0 Days, 04:45:33
    Description: R15_R16_CC
    Interface:
      bundle-250.1200
        Mode: vlan, Vlan-Id: 1200
        Operational state: up
        L2 MTU: 9086
        Counters:
          RX octets:                           32001923326315 (3055.70 Mbps)
          RX packets:                            128007768904
          TX octets:                                  3714362 (0.00 Mbps)
          TX packets:                                   26801

    Pseudowire:
        neighbor address: 100.0.15.15, pw-id: 15161
          PW state: up, Time in state: 0 Days, 04:44:10
          signaling protocol: LDP
          remote AC description: ge100-0/0/0.2424
          PW Transport Next Hop: auto_tunnel_CORE_R15_R16_1002
          Ignore-mtu-mismatch: enabled, ignore-encapsulation-mismatch: disabled
          steer-path: enabled, rsvp-te: tun9, no-fallback: enabled

          Counters:
            RX octets:                                4623965 (10.00 Mbps)
            RX packets:                                 26792
            TX octets:                         27654469343587 (3.2 Mbps)
            TX packets:                           97374943817

          +---------------------+---------------------+---------------------+---------------------+
          |                     | Local               | Remote              | Negotiated          |
          +---------------------+---------------------+---------------------+---------------------+
          | Label               | 309408              | 168895              | N/A                 |
          | MTU                 | 9086                | 9086                | N/A                 |
          | Control Word        | Present             | Present             | Present             |
          | Encapsulation       | Tagged              | Tagged              | Tagged              |
          | Status Support      | Supported           | Supported           | Supported           |
          | Last Status Code    | 0x0                 | 0x0                 | N/A                 |
          | FAT Label           | Rx, Tx              | Rx, Tx              | Rx, Tx              |
          +---------------------+---------------------+---------------------+---------------------+


    dnRouter# show vpws detail state down

    VPWS: R15_R16_1
    Admin state: enabled, Operational state: down, Time in state: 0 Days, 04:45:33
    Description:
    Interface:
      bundle-250.1201
        Mode: vlan, Vlan-Id: 1201
        Operational state: up
        L2 MTU: 9086
        Counters:
          RX octets:                           32001923326315 (3055.70 Mbps)
          RX packets:                            128007768904
          TX octets:                                  3714362 (0.00 Mbps)
          TX packets:                                   26801

    Pseudowire:
        neighbor address: 100.0.15.15, pw-id: 15161
          PW state: remote-not-ready, Time in state: 0 Days, 04:44:10
          signaling protocol: LDP
          remote AC description:
          PW Transport Next Hop:
          Ignore-mtu-mismatch: enabled, ignore-encapsulation-mismatch: disabled
          steer-path: enabled, rsvp-te: tun9, no-fallback: enabled

          Counters:
            RX octets:                                4623965 (0.00 Mbps)
            RX packets:                                 26792
            TX octets:                         27654469343587 (0.00 Mbps)
            TX packets:                           97374943817

          +---------------------+---------------------+---------------------+---------------------+
          |                     | Local               | Remote              | Negotiated          |
          +---------------------+---------------------+---------------------+---------------------+
          | Label               | 0                   | 0                   | N/A                 |
          | MTU                 | 9086                | 0                   | N/A                 |
          | Control Word        | Present             | Not Present         | Present             |
          | Encapsulation       | Tagged              | Tagged              | N/A                 |
          | Status Support      | Supported           | Not Supported       | Supported           |
          | Last Status Code    | 0x10                | 0x0                 | N/A                 |
          | FAT Label           | Rx, Tx              | Not supported       | Not supported       |
          +---------------------+---------------------+---------------------+---------------------+

.. **Help line:** show vpws detail

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
