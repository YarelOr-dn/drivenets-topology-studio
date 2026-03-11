routing-policy prefix-list rule
-------------------------------

**Minimum user role:** operator

To configure prefix-list entries for IPv4 or IPv6 address family:

**Command syntax: rule [rule-id] [rule-type] [ip-prefix]** matching-len {ge [ge-value] le [le-value] \| eq [eq-value]}

**Command mode:** config

**Hierarchies**

- routing-policy prefix-list ipv4|ipv6

**Note:**

Matching-len ge 3 le 32 means range 3-32.

.. Lower rule id is a higher priority rule

.. The rule id of 300000 is a default rule automatically assign by the system to deny any when no match was found.

.. Ip-prefix address-family must match the prefix list address-family

.. use matching-len to tune match for the subnet-mask.

.. must le-value >= ge-value.

.. cannot set le or ge together with eq

.. When configuring already configured rule-id, all of its entry is overwritten

.. The length specified by the range must be equal or longer than the length of the initial prefix.

.. no commands remove a specific rule entry by specifying the rule or by specifying rule sequence

**Parameter table**

+-----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+
| Parameter       | Description                                                                                                                                                                                                       | Range                        |
+=================+===================================================================================================================================================================================================================+==============================+
|                 |                                                                                                                                                                                                                   |                              |
| rule-id         | The rule's unique identifier within the prefix-list. It determines   the priority of the rule (rules with a low ID number have priority over rules   with high ID numbers). You must configure at least one rule. | 1..299999                    |
|                 |                                                                                                                                                                                                                   |                              |
|                 | The default ID (300000) is assigned by the system to "Deny   any" when no match is found.                                                                                                                         |                              |
|                 |                                                                                                                                                                                                                   |                              |
|                 | When configuring a rule ID that is already in use, all of the original rules' entries are overwritten.                                                                                                            |                              |
+-----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+
|                 |                                                                                                                                                                                                                   | allow                        |
| rule-type       | Defines whether the traffic matching the rule conditions are to be allowed or denied.                                                                                                                             | deny                         |
+-----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+
|                 | IPv4 or IPv6 prefix to match; any matches any prefix. The address family must match the prefix list address-family.                                                                                               | A.B.C.D/x                    |
| ip-prefix       |                                                                                                                                                                                                                   | xx:xx::xx:xx/x               |
|                 |                                                                                                                                                                                                                   | any                          |
+-----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+
|                 | The range for tuning the match for the subnet mask.                                                                                                                                                               | For all values (ge, le, eq): |
| matching-len    | ge - greater or equal                                                                                                                                                                                             | 0..32 for IPv4               |
|                 | le - lower or equal                                                                                                                                                                                               | 0..128 for IPV6              |
|                 | eq - equal                                                                                                                                                                                                        |                              |
|                 | - le value must be ≥ ge value                                                                                                                                                                                     |                              |
|                 | - You cannot set le or ge together with eq                                                                                                                                                                        |                              |
+-----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# prefix-list ipv4 PL_ALLOW_ANY
	dnRouter(cfg-rpl-pl)# rule 4000000 allow any

	dnRouter(cfg-rpl)# prefix-list ipv4 PL_MARTIANS
	dnRouter(cfg-rpl-pl)# rule 10 allow 0.64.0.0/10

	dnRouter(cfg-rpl-pl)# rule 20 allow 192.0.0.0/24
	dnRouter(cfg-rpl-pl)# rule 10 deny 10.0.0.0/24

	dnRouter(cfg-rpl-pl)# rule 30 allow 224.0.0.0/3 matching-len ge 3 le 32
	dnRouter(cfg-rpl-pl)# rule 5 allow 0.0.0.0/0 matching-len ge 24 le 32

	dnRouter(cfg-rpl-pl)# rule 10 allow.0.0.0/8 matching-len eq 24

	dnRouter(cfg-rpl-pl)# rule 30 deny 224.0.0.0/3 matching-len ge 4 le 32
	dnRouter(cfg-rpl-pl)# rule 5 deny 0.0.0.0/0 matching-len ge 24 le 32



**Removing Configuration**

To remove a rule entry:
::

	dnRouter(cfg-rpl)# prefix-list ipv6 PL6_MARTIANS
	dnRouter(cfg-rpl-pl6)# no rule 20

	dnRouter(cfg-rpl)# prefix-list ipv4 PL_ALLOW_ANY
	dnRouter(cfg-rpl-pl)# no rule 20

.. Help line:** Configure prefix-list entry

**Command History**

+-------------+---------------------------------------+
|             |                                       |
| Release     | Modification                          |
+=============+=======================================+
|             |                                       |
| 6.0         | Command introduced                    |
+-------------+---------------------------------------+
|             |                                       |
| 11.0        | Updated matching-len range syntax     |
+-------------+---------------------------------------+
| 17.0        | Updated rule-id to maximum 299999     |
+-------------+---------------------------------------+
