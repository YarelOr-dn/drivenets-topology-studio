traffic-engineering pcep pce
----------------------------

**Minimum user role:** operator

A path computation element (PCE) is a network entity that is able to calculate a network path based on the network topology.  Only one PCE is operational at any given time. This is the primary PCE. Any other PCE is a backup PCE that will only come into play if the primary PCE fails. You can configure up to 5 PCE servers. The PCE with the higher priority (lower configured priority value) will serve as the primary PCE. All other configured PCEs will serve as backups.

A backup PCE does not control LSPs (whether locally initiated by the PCC or by the PCE), but is reported by the PCC on the PCC-initiated LSP status. Similarly, the PCC will not act upon receiving LSP paths from the backup PCE.
Following a switchover between primary and backup PCE (after session disconnection and timers expiry), there will be no preemption when the primary PCE becomes the backup PCE. If the primary PCE returns to operation before redelegation of the backup PCE is established, the delegation of the primary PCE is preserved.

You can configure up to 5 PCE servers.

To configure the PCE server priority and address and enter its configuration mode:


**Command syntax: pce priority [priority] address [ip-address]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep

**Parameter table**

+---------------+---------------------------------------------------------------------------------------------------------------------------------+------------+-------------+
|               |                                                                                                                                 |            |             |
| Parameter     | Description                                                                                                                     | Range      | Default     |
+===============+=================================================================================================================================+============+=============+
|               |                                                                                                                                 |            |             |
| priority      | The PCE's priority. A lower value denotes a   higher priority PCE. The PCE with a highest priority serves as the primary   PCE. | 1..255     | \-          |
|               |                                                                                                                                 |            |             |
|               | You can configure up to 5 PCE servers, but their   priority must be unique.                                                     |            |             |
+---------------+---------------------------------------------------------------------------------------------------------------------------------+------------+-------------+
|               |                                                                                                                                 |            |             |
| ip-address    | The IP address of the PCE server. The IP address   is unique among the PCE servers.                                             | A.B.C.D    | \-          |
+---------------+---------------------------------------------------------------------------------------------------------------------------------+------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# pce priority 1 address 1.1.1.1
	dnRouter(cfg-mpls-te-pcep)# pce priority 2 address 2.2.2.2
	dnRouter(cfg-mpls-te-pcep)# pce priority 3 address 3.3.3.3
	dnRouter(cfg-te-pcep-pce)#

**Removing Configuration**

To remove the PCE server configuration:
::

	dnRouter(cfg-mpls-te-pcep)# no pce priority 3


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+