routing-policy as-path-list rule regex
--------------------------------------

**Minimum user role:** operator

This command matches the BGP AS path using regular expressions.

**Command syntax: rule [rule-id] [rule_type] regex [regex]**

**Command mode:** config

**Hierarchies**

- Routing-policy as-path-list

**Note:**

-  A lower rule-id results in higher priority

-  If no match was found, the AS number will be denied.

-  Rule 65535 is reserved as default rule of deny any as-number

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# as-path-list ASP_LOCAL
	dnRouter(cfg-rpl-asp)# rule 10 allow regex _64[5-9][0-9][0-9]_

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# as-path-list ASP_LOCAL
	dnRouter(cfg-rpl-asp)# rule 20 allow regex _6555[0-1]_

**Parameter table**

+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| Parameter | Description                                                                                                                                                                                                      | Range   |
+===========+==================================================================================================================================================================================================================+=========+
| rule-id   | The rule's unique identifier within the community list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule. | 1-65534 |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| rule-type | Defines whether the traffic matching the rule conditions are to be allowed or denied.                                                                                                                            | allow   |
|           |                                                                                                                                                                                                                  |         |
|           |                                                                                                                                                                                                                  | deny    |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| regex     | A regular expression defining a search pattern to match communities attribute in BGP updates. See Regular Expressions.                                                                                           | \-      |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+

**Removing Configuration**

To remove the as-path rule entry:
::

		dnRouter(cfg-rpl-asp)# no rule 20

.. **Help line:** add as-number regular-expression to as-path access list

**Command History**

+---------+------------------------------------------------------------------------------------+
| Release | Modification                                                                       |
+=========+====================================================================================+
| 6.0     | Command introduced                                                                 |
+---------+------------------------------------------------------------------------------------+
| 11.0    | Updated rule-id range to max 65534 as rule 65535 is reserved for the default rule. |
+---------+------------------------------------------------------------------------------------+