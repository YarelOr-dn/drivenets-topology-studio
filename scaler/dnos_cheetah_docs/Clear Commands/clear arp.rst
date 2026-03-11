clear arp
----------
**Minimum user role:** operator

To delete dynamic routes from the ARP table, use the following command:

**Command syntax: clear arp** vrf [vrf-name] interface [interface-name] ipv4-address [ipv4-host-address]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - clear arp - clears all dynamic arp entries in table

 - clear arp interface - clears all dynamic arp entries for specific interface

 - clear arp ipv4-address - clears dynamic arp entry for specific ipv4-address in a specific interface

 - clear arp - clears all dynamic ARP entries under default VRF

 - clear arp vrf - clears dynamic ARP entries for a specific VRF. It is not possible to specify 'all' to clear all dynamic ARP entries from all VRFs.

 - clear arp interface - clears all dynamic ARP entries for a specific interface. when VRF filter is used before, then only relevant interfaces under the specified VRF will be suggested

 - clear arp ipv4-address - clears dynamic ARP entry for a specific ipv4-address in a specific interface

.. **Help line:** clear dynamic arp entries

**Parameter table**

+----------------------+---------------------------------------------------------------------------+-----------------------------------------------------------------------------+-------------+
|                      |                                                                           |                                                                             |             |
| Parameter            | Description                                                               | Range                                                                       | Default     |
+======================+===========================================================================+=============================================================================+=============+
|                      |                                                                           |                                                                             |             |
| interface-name       | The name of the interface for which you want to clear all ARP entries     | ge<interface speed>-<A>/<B>/<C>                                             | \-          |
|                      |                                                                           |                                                                             |             |
|                      |                                                                           | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>                          |             |
|                      |                                                                           |                                                                             |             |
|                      |                                                                           | bundle-<bundle id>                                                          |             |
|                      |                                                                           |                                                                             |             |
|                      |                                                                           | bundle-<bundle id>.<sub-interface id>, mgmt0, mgmt-ncc-0, mgmt-ncc-1        |             |
+----------------------+---------------------------------------------------------------------------+-----------------------------------------------------------------------------+-------------+
|                      |                                                                           |                                                                             |             |
| ip4v-host-address    | The IPv4 (A.B.C.D) address for which you want to clear all ARP entries    | A.B.C.D                                                                     | \-          |
+----------------------+---------------------------------------------------------------------------+-----------------------------------------------------------------------------+-------------+
| vrf-name             | The name of the specific vrf for which you want to clear all ARP entries  | default, mgmt0, mgmt-ncc-0, mgmt-ncc-1, etc                                 | default     |
+----------------------+---------------------------------------------------------------------------+-----------------------------------------------------------------------------+-------------+

**Example**
::

	dnRouter# clear arp
	dnRouter# clear arp vrf My_VRF
	dnRouter# clear arp interfaces ge100-1/8/1
	dnRouter# clear arp interfaces ge100-1/8/1 ipv4-address 1.2.3.4

**Command History**

+-------------+--------------------------------------------------------+
| Release     | Modification                                           |
+=============+========================================================+
| 5.1.0       | Command introduced                                     |
+-------------+--------------------------------------------------------+
| 16.1        | Added support to clear arp entries per vrf instance    |
+-------------+--------------------------------------------------------+
