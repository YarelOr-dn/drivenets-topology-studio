# DNOS Prefix-list Configuration Reference

This document contains the complete DNOS CLI Prefix-list configuration syntax from the official DriveNets documentation.

---

## routing-policy prefix-list description
```rst
routing-policy prefix-list description
--------------------------------------

**Minimum user role:** operator

To add a description for your prefix list:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- routing-policy prefix-list ipv4
- routing-policy prefix-list ipv6

**Parameter table:**

+----------------+------------------------------------------------------------------------------------------------------------------------------------------+-----------------------+
|                |                                                                                                                                          |                       |
| Parameter      | Description                                                                                                                              | Range                 |
+================+==========================================================================================================================================+=======================+
|                |                                                                                                                                          |                       |
| description    | Enter a description for the   IP prefix-list.                                                                                            | 1..255 characters     |
|                |                                                                                                                                          |                       |
|                | Enter free-text description with spaces in between quotation   marks. If you do not use quotation marks, do not use spaces. For example: |                       |
|                |                                                                                                                                          |                       |
|                | ... description "My long description"                                                                                                    |                       |
|                |                                                                                                                                          |                       |
|                | ... description My_long_description                                                                                                      |                       |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+-----------------------+
| rule-type      | Defines whether the traffic matching the rule conditions are to be allowed or denied.                                                    | allow deny            |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+-----------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# prefix-list ipv4 PL_MARTIANS
	dnRouter(cfg-rpl-pl)# description MyDescription

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# prefix-list ipv6 PL6_MARTIANS
	dnRouter(cfg-rpl-pl6)# description MyDescription


**Removing Configuration**

To delete the description:
::

	dnRouter(cfg-rpl-pl6)# no description

.. **Help line:** Add description for an ip prefix-list

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+
```

## routing-policy prefix-list
```rst
routing-policy prefix-list
---------------------------

**Minimum user role:** operator

The prefix-list contains one or more ordered entries that are processed sequentially. To create a prefix-list and enter its configuration mode:

**Command syntax: prefix-list ipv4|ipv6 [prefix-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note:**

- Notice the change in prompt from dnRouter(cfg-rpl)#  to dnRouter(cfg-rpl-pl)#  (prefix-list configuration mode). When entering IPv6 prefix-list configuration mode, the prompt is dnRouter(cfg-rpl-pl6)#

- You cannot delete a prefix list that is being used by another policy or protocol.

- An empty prefix-list(no rules) would act as MATCH-ALL

..  no commands remove the prefix-list configuration for all prefix-list of specific address-family or for a specific prefix-list

.. validation:

.. if a user tries to remove a prefix-list while it is attached to any policy or protocol, the following error should be displayed:

.. "Error: unable to remove prefix-list <ip-prefix-list-name>. prefix-list is attached to policy <policy-name>".

..   or

.. "Error: unable to remove prefix-list <ip-prefix-list-name>. prefix-list is attached to protocol {BGP,OSPF,LDP} with <configuration> attachment point".

**Parameter table**

+------------------+------------------------------------+--------+---------+
| Parameter        | Description                        | Range  | Default |
+==================+====================================+========+=========+
| prefix-list-name | Provide a name for the prefix list | String | \-      |
|                  |                                    | 1..255 |         |
+------------------+------------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# prefix-list ipv4 PL_MARTIANS
	dnRouter(cfg-rpl-pl)#

	dnRouter(cfg-rpl)# prefix-list ipv6 PL_MARTIANS
	dnRouter(cfg-rpl-pl6)#


.. **Help line:** Configure ip prefix-list

**Removing Configuration**

To remove the prefix-list configuration for all prefix lists of a specific address-family:
::

	dnRouter(cfg-rpl)# no prefix-list ipv4

To remove a specific prefix-list:
::

	dnRouter(cfg-rpl)# no prefix-list ipv6 PL_MARTIANS

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+```

## routing-policy prefix-list rule
```rst
routing-policy prefix-list rule
-------------------------------

**Minimum user role:** operator

To configure prefix-list entries for IPv4 or IPv6 address family:

**Command syntax: rule [rule-id] [rule-type] [ip-prefix]** matching-len {ge [ge-value] le [le-value] \| eq [eq-value]}

**Command mode:** config

**Hierarchies**

- routing-policy prefix-list ipv4
- routing-policy prefix-list ipv6

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
```

