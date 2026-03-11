interfaces ipv6-address
------------------------

**Command syntax: ipv6-address {[ipv6-address] \| dhcp}**

**Description:** configure interface ipv6 address

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# ge100-1/1/1
	dnRouter(cfg-if-ge100-1/1/1)# ipv6-address 2001:ab12::1/127

	dnRouter(cfg-if)# mgmt-ncc-0
	dnRouter(cfg-if-mgmt-ncc-0)# ipv6-address dhcp


	dnRouter(cfg-if-ge100-1/1/1)# no ipv6-address

	dnRouter(cfg-if)# mgmt0
	dnRouter(cfg-if-mgmt0)# ipv6-address 2001:ab12::1/127


**Command mode:** config

**TACACS role:** operator

**Note:**

no commands remove the ipv6-address configuration

Loopback interface can be configured only with /128 (as in IPv4 with /32)

For convenience, an IPv6 address may be abbreviated to shorter notations by application of the following rules.

-  DHCP can be configured for mgmt-ncc-0 and/or mgmt-ncc-1 interfaces only

-  Both DHCP and static IP address cannot be configured on the same interfaces. Last configuration will override the previous one

-  One or more `leading zeroes <https://en.wikipedia.org/wiki/Leading_zero>` from any groups of hexadecimal digits are removed; this is usually done to either all or none of the leading zeroes. For example, the group *0042* is converted to *42*.

-  Consecutive sections of zeroes are replaced with a double colon (::). The double colon may only be used once in an address, as multiple use would render the address indeterminate. `RFC 5952 <https://tools.ietf.org/html/rfc5952>` recommends that a double colon must not be used to denote an omitted single section of zeroes.  `[38] <https://en.wikipedia.org/wiki/IPv6#cite_note-rfc5952sec422-38>`

An example of application of these rules:

Initial address: 2001:0db8:0000:0000:0000:ff00:0042:8329

   After removing all leading zeroes in each group: 2001:db8:0:0:0:ff00:42:8329

After omitting consecutive sections of zeroes: 2001:db8::ff00:42:8329

   The loopback address, 0000:0000:0000:0000:0000:0000:0000:0001, may be abbreviated to::1 by using both rules.

   As an IPv6 address may have more than one representation, the IETF has issued a  `proposed standard for representing them in text <https://en.wikipedia.org/wiki/IPv6_address#Recommended_representation_as_text>`.  `[39] <https://en.wikipedia.org/wiki/IPv6#cite_note-rfc5952-39>`

**Help line:** Configure interface ipv6 address

**Parameter table:**

+----------------+---------------------------------------+---------------+
| Parameter      | Values                                | Default value |
+================+=======================================+===============+
| ipv6-address   | {ipv6-address format}                 |               |
+----------------+---------------------------------------+---------------+
| Interface-name | bundle-<bundle id>                    |               |
|                |                                       |               |
|                | bundle-<bundle id>.<sub-interface id> |               |
|                |                                       |               |
|                | ge<interface speed>-<A>/<B>/<C>       |               |
|                |                                       |               |
|                | geX-<f>/<n>/<p>.<sub-interface id>    |               |
|                |                                       |               |
|                | lo<lo-interface id>                   |               |
|                |                                       |               |
|                | mgmt0                                 |               |
|                |                                       |               |
|                | mgmt-ncc-0, mgmt-ncc-1                |               |
+----------------+---------------------------------------+---------------+
