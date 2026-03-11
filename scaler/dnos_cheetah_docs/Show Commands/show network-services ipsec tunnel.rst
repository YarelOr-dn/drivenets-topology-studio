show network-services ipsec tunnel
----------------------------------

**Minimum user role:** viewer

To show state of IPSec tunnel

**Command syntax: show network-services ipsec tunnel [tunnel-id]**

**Command mode:** operational

**Example**
::

	dnRouter# show network-services ipsec tunnel 1

    Tunnel-ID: 1
      Tunnel Status: up,  Tunnel Uptime: 1 days, 10:52:00
      Down Reason: N/A
      Last Down Timestamp: 28-Sep-2022 06:10:13 UTC
      Description: Branch to main office tunnel

      Internal Interface: ipsec-0
        VLAN: 1000
        Resource: ipsec-resource-1
      External Interface: ipsec-1
        VLAN: 2000
        Resource: ipsec-resource-1

      IKE Map: MyIkeMap
      Device Public IP: 12.1.1.1
      Remote Public IP: 1.1.1.1
      Local Network:
        IP Prefix: 10.10.10.0/24
        Static Administrative Distance: 20
        IP Prefix: 11.11.11.0/24
        Static Administrative Distance: 20


      IKE SA (Phase 1):
        SA Status: up
        Inbound SPI: 325714191
        Outbound SPI: 23523
        Rekey Interval: 14400s
        Reauth Interval: 0
        Remaining Key Lifetime: 1240s
        Remaining Auth Lifetime: N/A

      IPsec SA (Phase 2):
        SA Status: up
        Inbound SPI: 12341
        Outbound SPI: 23514323
        Rekey Interval: 3600s
        Remaining Key Lifetime: 120s
        Anti Replay Window Size: 32, ESN: no




.. **Help line:** show IPSec tunnel data

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
