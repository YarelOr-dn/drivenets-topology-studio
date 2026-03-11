show bgp nsr
------------

**Minimum user role:** viewer

For information on BGP NSR, see "bgp nsr".

To display detailed information on the BGP non-stop-routing state:


**Command syntax: show bgp nsr**

**Command mode:** operational



**Note**

- NSR state - either ready or not-ready
- Reason - either N/A (for ready state), in-sync or not-connected (for not-ready state)


**Parameter table**

The following NSR information is displayed:

+------------------------------------+------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter                          | Description                                                                                                            | Range                                                                                                                                                                                                       |
+====================================+========================================================================================================================+=============================================================================================================================================================================================================+
| NSR configuration                  | Shows whether NSR is enabled or disabled.                                                                              | Enabled                                                                                                                                                                                                     |
|                                    |                                                                                                                        | Disabled                                                                                                                                                                                                    |
+------------------------------------+------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NSR state                          | Shows whether or not BGP NSR is ready. The NSR state is reflected only if NSR recovery on the standby NCC is possible. | Ready                                                                                                                                                                                                       |
|                                    |                                                                                                                        | Not Ready (see reason)                                                                                                                                                                                      |
+------------------------------------+------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Reason                             | Displays the reason why the NSR state is Not Ready                                                                     | not connected - the standby DB is disconnected                                                                                                                                                              |
|                                    | Applicable when the NSR state is "Not Ready"                                                                           | in-sync - the standby DB is synchronizing                                                                                                                                                                   |
+------------------------------------+------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Number of NSR capable BGP sessions | Displays the number of NSR-capable peers out of the total established peers.                                           | x out of y                                                                                                                                                                                                  |
|                                    | The number is displayed per VRF                                                                                        | Peers that have an IP address that is not supported by NSR (e.g. flowspec, link-state) and peers that support graceful restart, are not protected by NSR. You can check via the show bgp neighbors command. |
+------------------------------------+------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NSR last recovery                  | Displays when the system has last performed BGP NSR recovery due to bgpd process recovery                              | Timestamp                                                                                                                                                                                                   |
+------------------------------------+------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show bgp nsr
	NSR configuration: enabled
	NSR state: ready    Since: 16-Mar-2020 06:36:25 UTC
	Reason: N/A

	Number of NSR capable BGP sessions: 132 of out 150
		vrf default: 132 out of 150
		vrf A: 2 out of 2

	NSR last recovery: N/A

.. **Help line:**

**Command History**

+---------+----------------------------------------------------------+
| Release | Modification                                             |
+=========+==========================================================+
| 13.0    | Command introduced                                       |
+---------+----------------------------------------------------------+
| 16.1    | Added display of the number of NSR-capable BGP sessions  |
+---------+----------------------------------------------------------+
