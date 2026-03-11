clear bgp neighbor stale-route - N/A for this version
-----------------------------------------------------

**Command syntax: clear bgp** instance vrf [vrf-name] **neighbor {  * \| external \| [neighbor-address] \| remote-as [as-number] \| group [group-name]}** [address-family] **stale-route**

**Description:** Clear stale routes received from bgp neighbor. apply for both GR and LLGR routes. resulting in routes withdraw.

 * - clear for all neighbors

external - clear for all ebgp neighbors

neighbor-address - clear a specific neighbor by neighbor address

remote-as - clear neighbor matching the remote-as

group - clear all neighbor from a neighbor-group

**CLI example:**
::

	dnRouter# clear bgp neighbor * stale-route
	dnRouter# clear bgp neighbor * ipv4-unicast stale-route
	
	dnRouter# clear bgp neighbor external stale-route
	dnRouter# clear bgp neighbor external ipv6-unicast stale-route
	
	dnRouter# clear bgp neighbor 7.7.7.7 stale-route
	dnRouter# clear bgp neighbor 7.7.7.7 ipv6-unicast stale-route
	
	dnRouter# clear bgp neighbor remote-as 64999 stale-route
	
	dnRouter# clear bgp neighbor group BGP_GROUP stale-route
	
	
	dnRouter# clear bgp instance vrf A neighbor * stale-route
	
**Command mode:** operational

**TACACS role:** operator

**Note:**

optional parameters must match the order in the command

address-family is optional , when not specified, clear for both address-families

**Help line:**

**Parameter table:**

+------------------+----------------------------+-------+
| Parameter        | Values                     | notes |
+==================+============================+=======+
| vrf-name         | string                     |       |
|                  |                            |       |
|                  | length 1-255               |       |
+------------------+----------------------------+-------+
| neighbor-address | A.B.C.D,                   |       |
|                  |                            |       |
|                  | ipv6 address format        |       |
+------------------+----------------------------+-------+
| as-number        | 1-4294967295               |       |
+------------------+----------------------------+-------+
| group-name       | string                     |       |
|                  |                            |       |
|                  | length 1-255               |       |
+------------------+----------------------------+-------+
| address-family   | ipv4-unicast, ipv6-unicast |       |
+------------------+----------------------------+-------+
