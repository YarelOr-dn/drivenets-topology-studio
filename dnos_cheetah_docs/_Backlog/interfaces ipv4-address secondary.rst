interfaces ipv4-address secondary - N/A for this version
--------------------------------------------------------

**Command syntax: ipv4-address [ipv4-address] secondary**

**Description:** configure an additional secondary ipv4 address for the interface

can configure up to 5 secondary ipv4-address for and interface

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# bundle-1
	dnRouter(cfg-if-bundle-1)# ipv4-address 1.1.1.1/24 secondary
	dnRouter(cfg-if-bundle-1)# ipv4-address 2.2.2.2/24 secondary
	
	
	dnRouter(cfg-if-bundle-1)# no ipv4-address 2.2.2.2/24 secondary
	dnRouter(cfg-if-bundle-1)# no ipv4-address 1.1.1.1/24
	
**Command mode:** config

**TACACS role:** operator

**Note:**

'no ipv4-address [ipv4-address] secondary' - remove address as secondary and set it as primary address

'no ipv4-address [ipv4-address]' - removes the specific ipv4-address configuration

Validations:

-  Does not apply for Loopback interface

-  User cannot configure /0 subnet mask

-  interface ip address should be unique across all interfaces in the same vrf

-  secondary ipv4-address cannot be used as the donor address for unnumbered interface.

-  interface with secondary ip address is not valid for ISIS, OSPF, RSVP, LDP, MPLS Traffic-engineering

-  Addresses should be in different subnets and should not share the same prefix

-  User cannot configure broadcast or subnet network address per subnet mask (the first and the last address from /1 up to /30 masks). For example, following commands are not valid:

dnRouter(cfg)# interface ge100-1/1/1 ipv4-address 192.168.1.0/24

Error: Bad mask /24 for address 192.168.1.0

dnRouter(cfg)# interface ge100-1/1/1 ipv4-address 192.168.1.255/24

Error: Bad mask /24 for address 192.168.1.255

dnRouter(cfg)# interface ge100-1/1/1 ipv4-address 192.168.1.192/26

Error: Bad mask /26 for address 192.168.1.192

dnRouter(cfg)# interface ge100-1/1/1 ipv4-address 192.168.1.255/26

Error: Bad mask /26 for address 192.168.1.255

**Help line:**

**Parameter table:**

+--------------+-----------+---------------+
| Parameter    | Values    | Default value |
+==============+===========+===============+
| ipv4-address | A.B.C.D/X |               |
+--------------+-----------+---------------+
