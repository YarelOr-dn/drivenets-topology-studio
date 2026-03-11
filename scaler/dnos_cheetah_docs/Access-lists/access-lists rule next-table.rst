access-lists rule next-table
-----------------------------

**Minimum user role:** operator

An access list rule can be defined to direct certain traffic to be handled by a different VRF other than that which the interface is associated with. This can be achieved by specifying the next-table vrf in access-lists configurations,
so that the configured vrf in the ACL is used for forwarding packets towards its destination. The result of the lookup of the next-table VRF will determine the next-hop for the packets. In some cases the look-up may result in an unreachable
destination or null0 and lead to the packets being dropped. If the result of the lookup is a static route redirect to yet another VRF the packet will be dropped as
chaining of redirections is not allowed.

Next-table configuration for forwarding packets is referred to as ACL Based Forwarding (ABF).

To configure the next-table VRF to which packets matching the rule will be redirected:

**Command syntax: rule [rule-id] allow** next-table [vrf-name]

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule

- access-lists ipv6 rule

**Note**

- Next-table action is allowed only for rule of type allow.

- Next-table VRF must be an existing VRF and may not be the current VRF or any of the management VRFs: mgmt0, mgmt-ncc-0/0 or mgmt-ncc-1/0.


**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                 |             |
| Parameter           | Description                                                                                                                                                                                                                                     | Range           | Default     |
+=====================+=================================================================================================================================================================================================================================================+=================+=============+
| rule-id             | The rule's unique identifier within the access-list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule in order to create an access-list. |                 |             |
|                     |                                                                                                                                                                                                                                                 | 1..65434        | 65535       |
|                     | The default ID (65535) is attached to the default access-list which is "Deny any".                                                                                                                                                              |                 |             |
|                     |                                                                                                                                                                                                                                                 |                 |             |
|                     | Rule ID 65534 is reserved for default-icmp for IPv4/IPv6 access-lists, which allows protocol type icmp-v4/icmp-v6 on any IP and port.                                                                                                           |                 |             |
|                     |                                                                                                                                                                                                                                                 |                 |             |
|                     | You can configure up to 2000 rules per access-list and up to 250,000 rules altogether per system.                                                                                                                                               |                 |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+
|                     | Defines whether the traffic matching the rule   conditions are to be allowed or denied.                                                                                                                                                         |                 |             |
| rule-type           |                                                                                                                                                                                                                                                 | allow           | \-          |
|                     |                                                                                                                                                                                                                                                 |                 |             |
|                     |                                                                                                                                                                                                                                                 | deny            |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                 |             |
| next-table          | The next-table VRF name to which packets matching the rule are redirected.                                                                                                                                                                      |  VRF Name       | \-          |
|                     |                                                                                                                                                                                                                                                 |                 |             |
|                     | The Next-table VRF must be an existing VRF and may not be the current VRF or any of the management VRFs: mgmt0, mgmt-ncc-0/0 or mgmt-ncc-1/0.                                                                                                   |                 |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 101 allow next-table VRF-1
	dnRouter(cfg-acl-ipv4)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv6)# rule 200 allow next-table VRF-2

	dnRouter(cfg-acl-ipv4)# no rule 101 allow next-table
	dnRouter(cfg-acl-ipv6)# no rule 200 allow next-table

**Removing Configuration**

To remove the rule configuration:
::

	dnRouter(cfg-acl-ipv6)# no rule 101 allow next-table

.. **Help line:** Configure access-lists rule redirected-to VRF name.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 17.0        | Command introduced    |
+-------------+-----------------------+