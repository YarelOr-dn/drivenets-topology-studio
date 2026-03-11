routing-policy as-path-list rule passes-through
-----------------------------------------------

**Minimum user role:** operator

This command checks whether or not the specified AS numbers match the BGP AS path.

**Command syntax: rule [rule-id] [rule_type] passes-through [passes-through-as]**

**Command mode:** config

**Hierarchies**

- Routing-policy as-path-list

**Note:**

-  If no match was found, the AS number will be denied.

-  Rule 65535 is reserved as default rule of deny any as-number

**Parameter table**

+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
| Parameter         | Description                                                                                                                                                                                                      | Range                     |
+===================+==================================================================================================================================================================================================================+===========================+
| rule-id           | The rule's unique identifier within the community list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule. | 1-65534                   |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
| rule-type         | Defines whether the traffic matching the rule conditions are to be allowed or denied.                                                                                                                            | allow                     |
|                   |                                                                                                                                                                                                                  | deny                      |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
| passes-through-as | verifies if the specified AS numbers match the BGP AS path. The value can be a specific AS number (e.g. 7677) or a range (e.g. 65000-65020).                                                                     | 0..4294967295 x-y (range) |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# as-path-list ASP_LOCAL
	dnRouter(cfg-rpl-asp)# rule 10 allow passes-through 65060
	dnRouter(cfg-rpl-asp)# rule 20 allow passes-through 65070
	dnRouter(cfg-rpl-asp)# rule 10 deny passes-through 65160
	
	
	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# as-path-list ASP_LOCAL
	dnRouter(cfg-rpl-asp)# rule 30 allow passes-through 65000-65100
	dnRouter(cfg-rpl-asp)# rule 30 allow passes-through 65000-65500
	dnRouter(cfg-rpl-asp)# rule 40 allow passes-through 65100
	
	
	
**Removing Configuration**

To remove the as-path rule entry:
::

		dnRouter(cfg-rpl-asp)# no as-path rule 10

.. **Help line:** add as number to as-path access list

**Command History** 

+---------+------------------------------------------------------------------------------------+
| Release | Modification                                                                       |
+=========+====================================================================================+
| 6.0     | Command introduced                                                                 |
+---------+------------------------------------------------------------------------------------+
| 11.0    | Updated rule-id range to max 65534 as rule 65535 is reserved for the default rule. |
+---------+------------------------------------------------------------------------------------+