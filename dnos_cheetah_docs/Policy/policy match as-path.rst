policy match as-path
--------------------

**Minimum user role:** operator

To check whether the route's AS path matches AS paths in the specified AS path access-list:

**Command syntax: match as-path [list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+--------------+------------------------------------------------------------------+----------------------+------------+
|              |                                                                  |                      |            |
| Parameter    | Description                                                      | Range                | Default    |
+==============+==================================================================+======================+============+
|              |                                                                  |                      |            |
| list-name    | The name of the AS-Path access-list with which to match AS path. | 1..255 characters    | \-         |
|              |                                                                  |                      |            |
|              | Routes without a matching AS path are ignored.                   |                      |            |
+--------------+------------------------------------------------------------------+----------------------+------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# match as-path LIST-1


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no match as-path


.. **Help line:** Tests whether the route's as-path matches

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+