policy set community-list
-------------------------

**Minimum user role:** operator

Modify the communities' values of the BGP route per provided community-list and list-option.

delete - when the communities' values of the BGP route match the communities in the community-list, the communities' values are deleted. When all the communities' values are removed, the communities' attribute of the BGP update is deleted.
delete-not-in - when the communities' value of the BGP route DOES NOT match the communities in the community-list, the communities' values are deleted. When all the communities' values are removed, the communities' attribute of the BGP update is deleted.
replace - replace the communities' value of the BGP route with allowed communities in the community-list.
additive - update the communities’ value of the BGP route and append the allowed communities in the community-list.

To modify the communities' values from the BGP communities attribute using a community-list:


**Command syntax: set community-list [community-list-name] [list-option]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- Support well-known communities defined by name.

- The command cannot be set under same rule together with set community.

- For a replace or an additive, the attached community-list does not contain: deny rules, regex rules, and communities defined with ranges.

**Parameter table**

+------------------------+----------------------------------------------------------------------------------------+---------------------------------------------------------------------------------+------------+
|                        |                                                                                        |                                                                                 |            |
| Parameter              | Description                                                                            | Range                                                                           | Default    |
+========================+========================================================================================+=================================================================================+============+
|                        |                                                                                        |                                                                                 |            |
| community-list-name    | The community list against which to match the communities' values of the BGP route     | 1..255 characters                                                               | \-         |
+------------------------+----------------------------------------------------------------------------------------+---------------------------------------------------------------------------------+------------+
|                        |                                                                                        |                                                                                 |            |
| list-option            | Instructs what to do with the communities' values                                      | delete - delete the communities' value in the list                              | \-         |
|                        |                                                                                        |                                                                                 |            |
|                        |                                                                                        | delete-not-in - delete communities' value not matching the community-list       |            |
|                        |                                                                                        |                                                                                 |            |
|                        |                                                                                        | replace - replace communities' value with allowed communities in list           |            |
|                        |                                                                                        |                                                                                 |            |
|                        |                                                                                        | additive - append communities with allowed communities in list                  |            |
|                        |                                                                                        |                                                                                 |            |
+------------------------+----------------------------------------------------------------------------------------+---------------------------------------------------------------------------------+------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set community-list CL_INTERNAL delete

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-10)# set community-list CL2_INTERNAL delete-not-in

	dnRouter(cfg-rpl-policy)# rule 30 allow
	dnRouter(cfg-rpl-policy-rule-10)# set community-list CL2_INTERNAL replace

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-10)# set community-list CL2_INTERNAL additive

**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set community-list


.. **Help line:** Deletes the communities value from the BGP communities attribute

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 6.0         | Command introduced    |
+-------------+-----------------------+
| 18.1        | Added replace and     |
|             | additive option       |
+-------------+-----------------------+
| 18.2        | Impose action order   |
|             | within route policy   |
|             | rule                  |
+-------------+-----------------------+