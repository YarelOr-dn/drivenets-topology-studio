policy set large-community-list
-------------------------------

**Minimum user role:** operator

Modify the large-communities values of the BGP route per provided large-community-list and list-option.

delete - When the large-communities value of the BGP route matches the large-communities in the large-ommunity-list, the large-ommunities value are deleted. When all the large-communities values are removed, the large-communities attribute of the BGP update is deleted.
delete-not-in - When the large-communities value of the BGP route DOES NOT matche the large-communities in the large-community-list, the large-communities value are deleted. When all the large-communities values are removed, the large-communities attribute of the BGP update is deleted.
replace - replace the large-communities value of the BGP route with allowed large-communities in the large-community-list.
additive - update the large-communities value of the BGP route and append the allowed large-communities in the large-community-list.

To modify the large-communities value from the BGP large-communities attribute using a large-ommunity-list:


**Command syntax: set large-community-list [large-community-list-name] [list-option]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- Within the same route policy rule, "set large-community-list" will be processed and imposed before "set large-community" action.

- For a replace or an additive, the attached large-community-list does not contain: deny rules, regex rules, and communities defined with ranges.

**Parameter table**

+------------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------+-------------+
|                              |                                                                                              |                                                                                           |             |
| Parameter                    | Description                                                                                  | Range                                                                                     | Default     |
+==============================+==============================================================================================+===========================================================================================+=============+
|                              |                                                                                              |                                                                                           |             |
| large-community-list-name    | The large community list against which to match the communities value of the BGP route       | 1..255 characters                                                                         | \-          |
+------------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------+-------------+
|                              |                                                                                              |                                                                                           |             |
| list-option                  | Instructs what to do with the large communities value                                        | delete - delete the large communities value in the list                                   | \-          |
|                              |                                                                                              |                                                                                           |             |
|                              |                                                                                              | delete-not-in - delete communities value not matching the community-list                  |             |
|                              |                                                                                              |                                                                                           |             |
|                              |                                                                                              | replace - replace large-communities value with allowed communities in list                |             |
|                              |                                                                                              |                                                                                           |             |
|                              |                                                                                              | additive - append large-communities with allowed large-communities in list                |             |
|                              |                                                                                              |                                                                                           |             |
+------------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------+-------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set large-community-list LARGE_CL_INTERNAL delete

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-10)# set large-community-list LARGE_CL2_INTERNAL delete-not-in

	dnRouter(cfg-rpl-policy)# rule 30 allow
	dnRouter(cfg-rpl-policy-rule-10)# set large-community-list LARGE_CL2_INTERNAL replace

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-10)# set large-community-list LARGE_CL2_INTERNAL additive

**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set large-community-list


.. **Help line:** Deletes the communities value from the BGP communities attribute

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 15.1        | Command introduced    |
+-------------+-----------------------+
| 18.2        | add replace and       |
|             | additive option       |
+-------------+-----------------------+
| 18.2        | Impose action order   |
|             | within route policy   |
|             | rule                  |
+-------------+-----------------------+