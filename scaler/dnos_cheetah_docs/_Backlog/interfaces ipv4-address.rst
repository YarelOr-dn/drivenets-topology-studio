interfaces ipv4-address
-----------------------

**Command syntax: ipv4-address {[ipv4-address] \| unnumbered [source-interface] \| dhcp}**

**Description:** configure interface ipv4 address

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# ge100-1/1/1
	dnRouter(cfg-if-ge100-1/1/1)# ipv4-address 1.2.3.4/22

	dnRouter(cfg-if)# bundle-1
	dnRouter(cfg-if-bundle-1)# ipv4-address 1.2.3.254/24

	dnRouter(cfg-if)# bundle-1.100
	dnRouter(cfg-if-bundle-1.100)# ipv4-address unnumbered lo2

	dnRouter(cfg-if)# mgmt-ncc-0
	dnRouter(cfg-if-mgmt-ncc-0)# ipv4-address dhcp

	dnRouter(cfg-if)# mgmt0
	dnRouter(cfg-if-mgmt0)# ipv4-address 1.2.3.4/24

	dnRouter(cfg-if)# gre-tunnel-0
	dnRouter(cfg-if-gre-0)# ipv4-address 10.10.10.0/31
	dnRouter(cfg-if-gre-0)# no ipv4-address

	dnRouter(cfg-if-ge100-1/1/1)# no ipv4-address

**Command mode:** config

**TACACS role:** operator

**Note:**

no commands remove the ipv4-address configuration

interface unnumbered is not supported in v10.

Validations:

-  Loopback interface can be configured only with /32

-  DHCP can be configured for mgmt-ncc-0 and/or mgmt-ncc-1 interfaces only

-  Both DHCP and static IP address cannot be configured on the same interfaces. Last configuration will override the previous one

-  DHCP is a default configuration for mgmt-ncc-0 and mgmt-ncc-1 interfaces

-  Unnumbered interface cannot be set as *source-interface-name* for another unnumbered interface or itself

-  Unnumbered *interface-name* and *source-interface-name* have to be attached to the same VRF

-  IP address cannot be changed/removed for the interface that was configured as source-interface (aka donor) for another interface

-  Interface that was configured as source-interface (aka donor) for another interface, cannot be removed

-  User cannot configure /0 subnet mask

-  User cannot configure broadcast or subnet network address per subnet mask (the first and the last address from /1 up to /30 masks). For example, following commands are not valid:

-  GRE tunnel interface can only be configured with an IPv4 address. No unnumbered or DHCP support

dnRouter(cfg)# interface ge100-1/1/1 ipv4-address 192.168.1.0/24

Error: Bad mask /24 for address 192.168.1.0

dnRouter(cfg)# interface ge100-1/1/1 ipv4-address 192.168.1.255/24

Error: Bad mask /24 for address 192.168.1.255

dnRouter(cfg)# interface ge100-1/1/1 ipv4-address 192.168.1.192/26

Error: Bad mask /26 for address 192.168.1.192

dnRouter(cfg)# interface ge100-1/1/1 ipv4-address 192.168.1.255/26

Error: Bad mask /26 for address 192.168.1.255

**Help line:** Configure interface ipv4 address

**Parameter table:**

+------------------+--------------------------------------------+---------------+
| Parameter        | Values                                     | Default value |
+==================+============================================+===============+
| ipv4-address     | A.B.C.D/X                                  |               |
+------------------+--------------------------------------------+---------------+
| Interface-name   | bundle-<bundle id>                         |               |
|                  |                                            |               |
|                  | bundle-<bundle id>.<sub-interface id>      |               |
|                  |                                            |               |
|                  | ge<interface speed>-<A>/<B>/<C>            |               |
|                  |                                            |               |
|                  | geX-<f>/<n>/<p>.<sub-interface id>         |               |
|                  |                                            |               |
|                  | lo<lo-interface id>                        |               |
|                  |                                            |               |
|                  | mgmt0                                      |               |
|                  |                                            |               |
|                  | mgmt-ncc-0, mgmt-ncc-1                     |               |
|                  |                                            |               |
|                  | gre-tunnel-<id>                            |               |
+------------------+--------------------------------------------+---------------+
| source-interface | Any interface in the same vrf (not itself) |               |
|                  |                                            |               |
|                  | ge<interface speed>-<A>/<B>/<C>            |               |
|                  |                                            |               |
|                  | geX-<f>/<n>/<p>.<sub-interface id>         |               |
|                  |                                            |               |
|                  | bundle-<bundle id>                         |               |
|                  |                                            |               |
|                  | bundle-<bundle id>.<sub-interface id>      |               |
|                  |                                            |               |
|                  | lo<lo-interface id>                        |               |
+------------------+--------------------------------------------+---------------+
