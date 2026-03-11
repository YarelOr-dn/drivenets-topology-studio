policy description
------------------

**Minimum user role:** operator

To add a description for the rule:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+----------------+--------------------------------------------------------------------------------------------------------------------------------------------+-----------------------+-------------+
|                |                                                                                                                                            |                       |             |
| Parameter      | Description                                                                                                                                | Range                 | Default     |
+================+============================================================================================================================================+=======================+=============+
|                |                                                                                                                                            |                       |             |
| description    | Enter a   description for the rule.                                                                                                        | 1..255 characters     | \-          |
|                |                                                                                                                                            |                       |             |
|                | Enter free-text description with spaces in   between quotation marks. If you do not use quotation marks, do not use   spaces. For example: |                       |             |
|                |                                                                                                                                            |                       |             |
|                | ... description "My long   description"                                                                                                    |                       |             |
|                |                                                                                                                                            |                       |             |
|                | ... description   My_long_description                                                                                                      |                       |             |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------+-----------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow 
	dnRouter(cfg-rpl-policy-rule-10)# description MyDescription_Rule10
	dnRouter(cfg-rpl-policy-rule-10)# exit
	dnRouter(cfg-rpl-policy)# rule 20 allow 
	dnRouter(cfg-rpl-policy-rule-20)# description MyDescription_Rule20


**Removing Configuration**

To remove the description:
::

	dnRouter(cfg-rpl-policy-rule-10)# no description


.. **Help line:** add policy description

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+