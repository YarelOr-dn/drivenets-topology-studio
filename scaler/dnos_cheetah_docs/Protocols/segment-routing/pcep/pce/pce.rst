protocols segment-routing pcep pce priority address
---------------------------------------------------

**Minimum user role:** operator

A path computation element (PCE) is a network entity that can calculate a network path based on the network topology.
Only one PCE is operational at any given time. This is the primary PCE.
Any other PCE is a backup PCE that will only come into play if the primary PCE fails.
You can configure up to 5 PCE servers. The PCE with the higher priority (lower configured priority value) will serve as the primary PCE.
All other configured PCEs will serve as backups.

A backup PCE does not control policy lsps (whether locally initiated by the PCC or by the PCE), but is reported by the PCC on the PCC-initiated LSP status. Similarly, the PCC will not act upon receiving LSP paths from the backup PCE.
Following a switchover between primary and backup PCE (after session disconnection and timers expiry), there will be no preemption when the primary PCE becomes the backup PCE.
If the primary PCE returns to operation before redelegation of the backup PCE is established, the delegation of the primary PCE is preserved.

To configure the PCE server priority and address and enter its configuration mode:

**Command syntax: pce priority [priority] address [ip-address]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep

**Note**

- Up to 5 pce servers can be configured

- All PCE servers of both segment-routing and mpls traffic-engineering must have different source+destination addresses.

**Parameter table**

+------------+------------------+---------+---------+
| Parameter  | Description      | Range   | Default |
+============+==================+=========+=========+
| priority   | pce priority     | 1-255   | \-      |
+------------+------------------+---------+---------+
| ip-address | pce ipv4-address | A.B.C.D | \-      |
+------------+------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)# pce priority 1 address 1.1.1.1


**Removing Configuration**

To remove the PCE server configuration:
::

    dnRouter(cfg-protocols-sr-pcep)# no pce priority 1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
