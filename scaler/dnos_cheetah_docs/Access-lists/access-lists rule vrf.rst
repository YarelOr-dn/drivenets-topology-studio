access-lists rule vrf
---------------------

**Minimum user role:** operator

To create an access-list to match a specific packet VRF context:

**Command syntax: rule [rule-id] [rule-type]** vrf [vrf-name]

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule

- access-lists ipv6 rule


**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                     |             |
| Rule Parameters     | Description                                                                                                                                                                                                                                     | Range               | Default     |
+=====================+=================================================================================================================================================================================================================================================+=====================+=============+
| rule-id             | The rule's unique identifier within the access-list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule in order to create an access-list. |                     |             |
|                     |                                                                                                                                                                                                                                                 | 1..65434            | 65535       |
|                     | The default ID (65535) is attached to the default access-list which is "Deny any".                                                                                                                                                              |                     |             |
|                     |                                                                                                                                                                                                                                                 |                     |             |
|                     | Rule ID 65534 is reserved for default-icmp for IPv4/IPv6 access-lists, which allows protocol type icmp-v4/icmp-v6 on any IP and port.                                                                                                           |                     |             |
|                     |                                                                                                                                                                                                                                                 |                     |             |
|                     | You can configure up to 2000 rules per access-list and up to 250,000 rules altogether per system.                                                                                                                                               |                     |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                     | Defines whether the traffic matching the rule conditions are to be allowed or denied.                                                                                                                                                           |                     |             |
| rule-type           |                                                                                                                                                                                                                                                 | allow               | \-          |
|                     |                                                                                                                                                                                                                                                 |                     |             |
|                     |                                                                                                                                                                                                                                                 | deny                |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                     |             |
| vrf-name            | Used to configure an access-list rule to match a configured vrf name                                                                                                                                                                            | string length 1-255 | Any         |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 100 allow vrf IN-BAND-CTRL
	dnRouter(cfg-acl-ipv4)# rule 101 allow src-ip 1.2.3.4/20 vrf CUSTOMER_A

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv6)# rule 10 deny src-ip 2001::1 vrf CUSTOMER_B

**Removing Configuration**

To delete a rule configuration:
::

	dnRouter(cfg-acl-ipv4)# no rule 101 allow vrf


.. **Help line:** Configure access-lists rule vrf

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 16.2        | Command introduced    |
+-------------+-----------------------+
