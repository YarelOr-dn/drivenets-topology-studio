interfaces ipv6-address secondary - N/A for this version
--------------------------------------------------------

**Command syntax: ipv6-address [ipv6-address] secondary**

**Description:** configure an additional secondary ipv6 address for the interface

can configure up tupdate o 5 secondary ipv6-address for and interface

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# bundle-1
	dnRouter(cfg-if-bundle-1)# ipv6-address 2001:ab12::1/127 secondary
	dnRouter(cfg-if-bundle-1)# ipv6-address 2002:cc53::1/64 secondary
	
	
	
	dnRouter(cfg-if-bundle-1)# no ipv6-address 2001:ab12::1/127
	
**Command mode:** config

**TACACS role:** operator

**Note:**

'no ipv6-address [ipv6-address] secondary' - remove address as secondary and set it as primary address

'no ipv6-address [ipv6-address]' - removes the specific secondary ipv6-address configuration

'no ipv6-address' - removes all ipv6-address configuration

Validations:

-  Does not apply for Loopback interface

-  secondary ipv6-address cannot be used as the donor address for unnumbered interface.

-  User cannot configure /0 subnet mask

-  interface ip address should be unique across all interfaces in the same vrf

-  interface with secondary ip address is not valid for ISIS, OSPF, RSVP, LDP, MPLS Traffic-engineering

-  Addresses should be in different subnets and should not share the same prefix

**Help line:**

**Parameter table:**

+--------------+-----------------------+---------------+
| Parameter    | Values                | Default value |
+==============+=======================+===============+
| ipv6-address | {ipv6-address format} |               |
+--------------+-----------------------+---------------+
