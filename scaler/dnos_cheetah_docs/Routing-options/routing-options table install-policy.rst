routing-options table install-policy
------------------------------------

**Minimum user role:** operator

he install-policy enables to filter out destinations from being installed in the MPLS-NH table according to a predefined prefix-list using a policy. This prevents specific recursive routes from entering the tunnel, regardless of the originating protocol.

To set an import policy to apply on routes being installed in the routing table:

**Command syntax: install-policy [policy-name]**

**Command mode:** config

**Hierarchies**

- routing-options table

.. **Note**

	- policy only support the following action: match ipv4|ipv6 prefix [prefix-list-name]

	- policy rule apply regardless of originating protocol (RSVP, LDP, IGP-Shortcuts)

	- no command removes the import policy

**Parameter table**

+-------------+-----------------------------------------------------------------------------------------------------------------------+--------+
| Parameter   | Description                                                                                                           | Range  |
+=============+=======================================================================================================================+========+
| policy-name | The name of the policy that you want applied to installed routes.                                                     | 1..255 |
|             | The policy only supports the following action: match ipv4|ipv6 prefix [prefix-list-name]. See policy match ip prefix. |        |
|             | The policy rule applies regardless of the originating protocol (RSVP, LDP, IGP-shortcuts).                            |        |
+-------------+-----------------------------------------------------------------------------------------------------------------------+--------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# table mpls-nh
	dnRouter(cfg-routing-option-mpls-nh)# install-policy MPLS_NH_IN
	
	
	

**Removing Configuration**

To remove the policy import:
::

	dnRouter(cfg-routing-option-mpls-nh)# no install-policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


