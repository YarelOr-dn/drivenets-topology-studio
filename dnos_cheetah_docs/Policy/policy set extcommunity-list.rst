policy set extcommunity-list
----------------------------

**Minimum user role:** operator

Modify the extcommunities' values of the BGP route per provided extcommunity-list and the list-option.

delete - when the extcommunities' values of the BGP route match the extcommunities in the extcommunity-list, the extcommunities' values are deleted. When all the extcommunities' values are removed, the extcommunities' attribute of the BGP update is deleted.
delete-not-in - when the extcommunities' values of the BGP route DO NOT match the extcommunities in the extcommunity-list, the extcommunities' values are deleted. When all the extommunities' values are removed, the extcommunities' attribute of the BGP update is deleted.
replace - replace the extcommunities' value of the BGP route with allowed extcommunities in the extcommunity-list.
additive - update the extcommunities' value of the BGP route and append the allowed extcommunities in the extcommunity-list.

To modify the extcommunities value from the BGP extcommunities attribute using a extcommunity-list:


**Command syntax: set extcommunity-list [extcommunity-list-name] [list-option]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

 - Expected extcommunity modification will be per modification action {additive | replace} and types of extcommunities specified in the list (color, rt, soo) i.e:

 - - replace: for a given type (color, rt, soo) specified in list, replace all extcommunities of same type with the extcommunities matching that type (other extcommunities type are not effected).

 - - additive: add the allowed extcommunities in list.

- Within the same route policy rule, "set extcommunity-list" will be processed and imposed before "set extcommunity" action.

- For a replace or an additive, the attached extcommunity-list does not contain: deny rules, regex rules, and extcommunities defined with ranges.

**Parameter table**

+---------------------------+-------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------+------------+
|                           |                                                                                                 |                                                                                 |            |
| Parameter                 | Description                                                                                     | Range                                                                           | Default    |
+===========================+=================================================================================================+=================================================================================+============+
|                           |                                                                                                 |                                                                                 |            |
| extcommunity-list-name    | The extended community list against which to match the communities' values of the BGP route.    | 1..255 characters                                                               | \-         |
+---------------------------+-------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------+------------+
|                           |                                                                                                 |                                                                                 |            |
| list-option               | Instructs what to do with the extcommunities' values                                            | delete - delete the extcommunities' value in the list                           | \-         |
|                           |                                                                                                 |                                                                                 |            |
|                           |                                                                                                 | delete-not-in - delete extcommunities' value not matching the extcommunity-list |            |
|                           |                                                                                                 |                                                                                 |            |
|                           |                                                                                                 | replace - replace extcommunities' value with allowed extcommunities in list     |            |
|                           |                                                                                                 |                                                                                 |            |
|                           |                                                                                                 | additive - append extcommunities with allowed communities in list               |            |
|                           |                                                                                                 |                                                                                 |            |
+---------------------------+-------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------+------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set extcommunity-list EXTCL_STRIP delete-not-in

	dnRouter(cfg-rpl-policy)# rule 30 allow
	dnRouter(cfg-rpl-policy-rule-10)# set extcommunity-list EXT_CL2_INTERNAL replace

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-10)# set extcommunity-list EXT_CL2_INTERNAL additive

**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set extcommunity-list


.. **Help line:** Deletes the communities value from the BGP communities attribute

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 6.0         | Command introduced    |
+-------------+-----------------------+
| 18.2        | add replace and       |
|             | additive option       |
+-------------+-----------------------+
| 18.2        | Impose action order   |
|             | within route policy   |
|             | rule                  |
+-------------+-----------------------+