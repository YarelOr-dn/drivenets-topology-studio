policy call
-----------

**Minimum user role:** operator

To jump to another policy after match and set action of this rule:

**Command syntax: call [policy-name]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+----------------+-----------------------------------------------+----------------------+------------+
|                |                                               |                      |            |
| Parameter      | Description                                   | Rule                 | Default    |
+================+===============================================+======================+============+
|                |                                               |                      |            |
| policy-name    | the name of the policy   to which to jump.    | 1..255 characters    | \-         |
+----------------+-----------------------------------------------+----------------------+------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy POL_A
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# call POL_B


**Removing Configuration**

To remove the policy call:
::

	dnRouter(cfg-rpl-policy-rule-10)# no call


.. **Help line:** Jump to another Policy after match+set action for this rule

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+