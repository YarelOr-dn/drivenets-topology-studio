policy rule
-----------

**Minimum user role:** operator

To create a new rule and enter its configuration hierarchy:

**Command syntax: rule [rule-id] [rule-type]**

**Command mode:** config

**Hierarchies**

- routing-policy policy

**Note**

-  You cannot configure 'set' actions under a 'deny' rule.

-  You can configure multiple different types of match or set under the same entry.

-  If more than one match condition is defined, all conditions must be met for the rule to apply.

-  Rule-id 65535 is the default rule assigned by the system, configured to deny any route.

-  There is no guarantee for the order in which configuration under a rule is applied. If ordering is needed it can be achieved by splitting the configuration into several rules and using the 'on-match next' functionality.


..
   -  for example:

   dnRouter(cfg-rpl-policy-rule-10)# match as-path LIST-1

   dnRouter(cfg-rpl-policy-rule-10)# match as-path LIST-2

   'match as-path LIST-2' will override the 'match as-path LIST-1' configuration

   dnRouter(cfg-rpl-policy-rule-10)# set as-path prepend 23456

   dnRouter(cfg-rpl-policy-rule-10)# set as-path prepend 12956

   'set as-path prepend 12956' will override the 'set as-path prepend 23456' configuration




**Parameter table**

+---------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|               |                                                                                                                                                                                                                   |             |             |
| Parameter     | Description                                                                                                                                                                                                       | Range       | Default     |
+===============+===================================================================================================================================================================================================================+=============+=============+
|               |                                                                                                                                                                                                                   |             |             |
| rule-id       | The rule's unique identifier within the route   map. It determines the priority of the rule (rules with a low ID number have   priority over rules with high ID numbers). You must configure at least one   rule. | 1..65534    | \-          |
|               |                                                                                                                                                                                                                   |             |             |
|               | The default ID (65535) is assigned by the system   to "Deny any" when no match is found.                                                                                                                          |             |             |
+---------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|               |                                                                                                                                                                                                                   |             |             |
| rule-type     | Defines whether the traffic matching the rule   conditions are to be allowed or denied.                                                                                                                           | allow       | \-          |
|               |                                                                                                                                                                                                                   |             |             |
|               |                                                                                                                                                                                                                   | deny        |             |
+---------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)#

	dnRouter(cfg-rpl-policy)# rule 20 deny
	dnRouter(cfg-rpl-policy-rule-20)#


**Removing Configuration**

To remove the rule entry:
::

	dnRouter(cfg-rpl-policy)# no rule 10


.. **Help line:** Create policy rule

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+