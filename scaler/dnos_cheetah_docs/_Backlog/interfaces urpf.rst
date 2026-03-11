interfaces urpf - N/A for this version
--------------------------------------

**Command syntax: urpf [urpf-type] [urpf-state]** allow-default

**Description:** configure interface uRPF. The purpose of uRPF is to verify incoming packets reachability by checking their source IP address. This action prevents IP address spoofing in unicast routing.

There are two operating modes:

-  strict mode - The packet source IP address must appear in the routing table with the incoming interface as the route next-hop

-  loose mode - The packet source IP address must appear in the routing table

allow-default parameter is an optional field which allows uRPF to resolve reverse path forwarding to a default route. The parameter can be added to strict mode or loose mode. If the parameter not added, the default route is not allowed at uRPF routing table

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	dnRouter(cfg-if)# ge100-1/1/1
	dnRouter(cfg-if-ge100-1/1/1)# urpf ipv4 strict
	dnRouter(cfg-if-ge100-1/1/1)# urpf ipv4 strict allow-default
	
	dnRouter(cfg-if)# bundle-1.100 
	dnRouter(cfg-if-bundle-1.100)# urpf ipv6 loose
	dnRouter(cfg-if-bundle-1.100)# urpf ipv6 loose allow-default
	
	dnRouter(cfg-if-bundle-1.100)# no urpf
	dnRouter(cfg-if-bundle-1.100)# no urpf ipv4
	dnRouter(cfg-if-ge100-1/1/1)# no urpf ipv6 loose allow-default
	
	
**Command mode:** config

**TACACS role:** operator

**Note:** no command disables urpf function per address family or per interface

**Help line:** Configure interface unicast reverse path forwarding

**Parameter table:**

+----------------+---------------------------------------+---------------+
| Parameter      | Values                                | Default value |
+================+=======================================+===============+
| urpf-type      | ipv4/ipv6                             |               |
+----------------+---------------------------------------+---------------+
| urpf-state     | strict/loose                          |               |
+----------------+---------------------------------------+---------------+
| allow-default  | allow-default                         |               |
+----------------+---------------------------------------+---------------+
| Interface-name | bundle-<bundle id>                    |               |
|                |                                       |               |
|                | bundle-<bundle id>.<sub-interface id> |               |
+----------------+---------------------------------------+---------------+
