policy set as-path exclude
--------------------------

**Minimum user role:** operator

To exclude the specified as-number(s) from the as-path:

**Command syntax: set as-path exclude [as-number],** [as-number], .

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- Running this command on a rule appends to the list and does not overwrite any previously configured AS number.

- Within the same route policy rule, "set as-path exclude" will be processed and imposed before "set as-path prepend" action

**Parameter table**

+---------------+--------------------------------------------------------------------------------------+---------------+---------+
|               |                                                                                      |               | Default |
| Parameter     | Description                                                                          | Range         |         |
+===============+======================================================================================+===============+=========+
|               |                                                                                      | 1..4294967295 | \-      |
| as-number     | the AS-number to exclude from the AS-path. You   can specify multiple AS numbers.    |               |         |
+---------------+--------------------------------------------------------------------------------------+---------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)#set as-path exclude 23456

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)#set as-path exclude 12956, 23456
	dnRouter(cfg-rpl-policy-rule-20)#set as-path exclude 5000


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-20)# no set as-path exclude


.. **Help line:** exclude the specified as-number(s) from the as-path

**Command History**

+-------------+---------------------------------------------+
|             |                                             |
| Release     | Modification                                |
+=============+=============================================+
|             |                                             |
| 6.0         | Command introduced                          |
+-------------+---------------------------------------------+
|             |                                             |
| 9.0         | Changed parameter's range from minimum 1    |
+-------------+---------------------------------------------+
|             |                                             |
| 18.2        | Impose action order within route policy rule|
+-------------+---------------------------------------------+