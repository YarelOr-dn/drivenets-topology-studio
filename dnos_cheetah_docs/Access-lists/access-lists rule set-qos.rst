access-lists rule set-qos
-------------------------

**Minimum user role:** operator

Extend ingress traffic-class-map definition for QoS actions according to access-list IP traffic match qualifiers.
For the matched flow, given the desired traffic-class-map is defined in the QoS ingress policy of the same interface ingress access-list, the flow will be imposed by the QoS behavior requested for that traffic-class-map that is defined in the QoS ingress policy.
Apply “default” to impose the default ingress QoS rule behavior on matched flow.

To configure the seq-qos with which packets matching the rule will be influenced:

**Command syntax: rule [rule-id] allow** {set-qos-traffic-class [traffic-class-map name] | set-qos-default}

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule allow

- access-lists ipv6 rule allow

**Note**
- set-qos-traffic-class <traffic-class-map name> is mutually exclusive with set-qos-default. Setting one will overwrite the other
- no commend will require to match the existing set option
- set-qos action is allowed only for rule of type allow.
- set-qos action is allowed only for ingress access-list.


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
| traffic-class-map   | A configured QoS traffic-class map                                                                                                                                                                                                              |  string         | \-          |
| name                |                                                                                                                                                                                                                                                 |                 |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 101 allow set-qos-traffic-class Class0
	dnRouter(cfg-acl-ipv4)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv6)# rule 200 allow set-qos-default

**Removing Configuration**

To remove the rule configuration:
::

	dnRouter(cfg-acl-ipv4)# no rule 101 allow set-qos-traffic-class
	dnRouter(cfg-acl-ipv6)# no rule 101 allow set-qos-default

.. **Help line:** Configure access-lists rule set-qos.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 18.2        | Command introduced    |
+-------------+-----------------------+
