show bgp nlri
-------------

**Minimum user role:** viewer

To display NLRIs per table:


**Command syntax: show bgp** instance vrf [vrf-name] **[address-family] [sub-address-family] nlri [nlri]** bestpath-compare

**Command mode:** operational


..
       **Internal Note**

       - use vrf to display routing information for a non-default vrf

       - use address-family, sub-address-family for specific afi-safi routes

       - nlri - require to use apostrophes when entring the nlri string

**Parameter table**

+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter          | Description                                                                                                                                                       | Range                       |
+====================+===================================================================================================================================================================+=============================+
| vrf-name           | Display routing information for a non-default VRF                                                                                                                 | 1..255 characters           |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                                   | IPv4                        |
|                    |                                                                                                                                                                   | IPv6                        |
|                    |                                                                                                                                                                   | Link-state                  |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                                    | flowspec                    |
|                    | N/A for link-state address-family                                                                                                                                 | rt-constrains               |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| nlri               | Filter the displayed information for a specific Network Layer Reachability Information (NLRI).                                                                    | \-                          |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| bestpath-compare   | Compares between each path and the overall best path                                                                                                              |                             |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

    dnRouter# show bgp ipv4 rt-constrains nlri 4200000000:15:1000

	Path #1
  	 Local
    	 0.0.0.0 from 0.0.0.0 (100.115.115.115)
    	Origin IGP, localpref 100, weight 32768, valid, sourced, local, best
    	RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
    	AddPath ID: RX 0, TX 2
    	Last update: 07-Oct-2021 15:22:25 UTC

.. **Help line:** show bgp rt-constrains nlri

**Command History**

+---------+-------------------------------------------------------------------------------+
| Release | Modification                                                                  |
+=========+===============================================================================+
| 10.0    | Command introduced                                                            |
+---------+-------------------------------------------------------------------------------+
| 13.0    | Added support for flowspec SAFI                                               |
+---------+-------------------------------------------------------------------------------+
| 16.1    | Added support for IPv4 Route Target Constrain SAFI and bestpath-compare knob  |
+---------+-------------------------------------------------------------------------------+
