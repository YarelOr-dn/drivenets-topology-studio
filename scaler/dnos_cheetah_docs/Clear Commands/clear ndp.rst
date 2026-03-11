clear ndp
----------

**Minimum user role:** operator

To delete dynamic routes from the NDP table, use the following command:

**Command syntax: clear ndp** vrf [vrf-name] interface [interface-name] ipv6-address [ipv6-host-address]

	dnRouter# clear ndp
	dnRouter# clear ndp vrf My_VRF
	dnRouter# clear ndp interfaces ge100-1/8/1
	dnRouter# clear ndp interfaces ge100-1/8/1 ipv6-address 2001:1234::1

**Command mode:** operation

.. **Hierarchies**

**Note**

- If you do not specify an [interface-name] or an [ipv6-host-address], all NDP entries will be cleared from the NDP table

- clear ndp vrf - clears dynamic NDP entries for a specific VRF. It is not possible to specify 'all' to clear all dynamic NDP entries from all VRFs.

.. - clear ndp - clears all dynamic NDP entries under default VRF

.. - clear ndp interface - clears all dynamic NDP entries for a specific interface. when VRF filter is used before, then only relevant interfaces under the specified VRF will be suggested

.. - clear ndp ipv6-address - clears dynamic NDP entry for specific ipv6-address for specific interface


**Parameter table:**

+-------------------+--------------------------------------------------------------------------+---------------+
| Parameter         | Values                                                                   | Default value |
+===================+==========================================================================+===============+
| interface-name    | ge<interface speed>-<A>/<B>/<C>                                          |               |
|                   |                                                                          |               |
|                   | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>                       |               |
|                   |                                                                          |               |
|                   | bundle-<bundle id>                                                       |               |
|                   |                                                                          |               |
|                   | bundle-<bundle id>.<sub-interface id>, mgmt0, mgmt-ncc-0, mgmt-ncc-1     |               |
+-------------------+--------------------------------------------------------------------------+---------------+
| ipv6-host-address | {ipv6-address format} as /128                                            |               |
+-------------------+--------------------------------------------------------------------------+---------------+
| vrf-name          | default, mgmt0, mgmt-ncc-0, mgmt-ncc-1, etc                              | default       |
+-------------------+--------------------------------------------------------------------------+---------------+

**Example**
::

	dnRouter# clear ndp
	dnRouter# clear ndp vrf My_VRF
	dnRouter# clear ndp interfaces ge100-1/8/1
	dnRouter# clear ndp interfaces ge100-1/8/1 ipv6-address 2001:1234::1


.. **Help line:** clear dynamic ndp entries

**Command History**

+-------------+--------------------------------------------------------+
| Release     | Modification                                           |
+=============+========================================================+
| 5.1.0       | Command introduced                                     |
+-------------+--------------------------------------------------------+
| 16.1        | Added support to clear ndp entries per vrf instance    |
+-------------+--------------------------------------------------------+
