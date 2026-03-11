ldp address-family discovery transport-address
----------------------------------------------

**Minimum user role:** operator

Sets the default LDP transport address for the address family. The LSR advertises the transport address in the transport address TLV of the LDP hello messages:

**Command syntax: discovery transport-address [ipv4-address]**

**Command mode:** config

**Hierarchies**

- protocols ldp address-family

**Note**

- The ipv4 address must be configured to use LDP.

.. - When transport-address is not configured the LSR shall send the LDP Router ID in the hello messages Transport address TLV.

.. - Upon transport-address configuration the source LSR shall add the Transport Address TLV to the hello message. The peer LSR will use the IPv4 address as appears in the TLV.

.. - 'no discovery trasnport-address' reverts the trasnport address to the default i.e. to the LDP Router id.

**Parameter table**

+-----------------+---------------------------------------------------------------+-------------+-------------+
|                 |                                                               |             |             |
| Parameter       | Description                                                   | Range       | Default     |
+=================+===============================================================+=============+=============+
|                 |                                                               |             |             |
| ipv4-address    | An arbitrary address advertised in LDP discovery messages.    |  A.B.C.D    | \-          |
+-----------------+---------------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# discovery transport-address 2.2.2.2

**Removing Configuration**

To revert to the default configuration (the LDP Router ID):
::

	dnRouter(cfg-protocols-ldp-afi)# no discovery transport-address

.. **Help line:** Sets the default LDP transport address for the address-family

**Command History**

+-------------+----------------------------------------+
|             |                                        |
| Release     | Modification                           |
+=============+========================================+
|             |                                        |
| 6.0         | Command introduced                     |
+-------------+----------------------------------------+
|             |                                        |
| 13.0        | Added Removing Configuration           |
+-------------+----------------------------------------+