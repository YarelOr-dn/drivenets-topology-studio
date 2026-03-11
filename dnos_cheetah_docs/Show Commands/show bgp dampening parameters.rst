show bgp dampening-parameters 
------------------------------

**Minimum user role:** viewer

The following command displays configured dampening parameters:



**Command syntax: show bgp** instance vrf [vrf-name] [address-family] [sub-address-family] **dampening-parameters**

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

	- address-family sub-address-family are optional, if not specified display for all sub-address-families

**Parameter table**

+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter          | Description                                                                                                                                             | Range                       |
+====================+=========================================================================================================================================================+=============================+
| vrf-name           | Display routing information for a non-default VRF                                                                                                       | 1..255 characters           |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                         | IPv4                        |
|                    |                                                                                                                                                         | IPv6                        |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                          | unicast                     |
|                    |                                                                                                                                                         | vpn                         |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp dampening-parameters
	
	dnRouter# show bgp instance vrf A dampening-parameters
	
	dnRouter# show bgp ipv4 unicast dampening-parameters
	
	dnRouter# show bgp ipv6 vpn dampening-parameters
	
	

.. **Help line:**

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 6.0     | Command introduced                 |
+---------+------------------------------------+

