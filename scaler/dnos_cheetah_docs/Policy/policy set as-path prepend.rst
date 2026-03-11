policy set as-path prepend
---------------------------

**Minimum user role:** operator

To prepend the given string of AS number(s) or last AS to the AS-path:

**Command syntax: set as-path prepend { as-number [as-number],** [as-number], . \| **last-as [number] }**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- This action is only relevant as a BGP policy.

- Within the same route policy rule, "set as-path exclude" will be processed and imposed before "set as-path prepend" action

**Parameter table**

+---------------+-------------------------------------------------------------------------------------+------------------+---------+
|               |                                                                                     |                  | Default |
| Parameter     | Description                                                                         | Range            |         |
+===============+=====================================================================================+==================+=========+
|               |                                                                                     |                  | \-      |
| as-number     | The AS number to prepend to the AS-path. You can   specify multiple AS numbers.     | 1..4294967295    |         |
+---------------+-------------------------------------------------------------------------------------+------------------+---------+
|               |                                                                                     |                  | \-      |
| number        | The number of times the last as-number will be added.                               | 1..9             |         |
+---------------+-------------------------------------------------------------------------------------+------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set as-path prepend as-number 23456
	dnRouter(cfg-rpl-policy-rule-10)# exit

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# set as-path prepend as-number 12956, 23456
	dnRouter(cfg-rpl-policy-rule-20)# exit

	dnRouter(cfg-rpl-policy)# rule 30 allow
	dnRouter(cfg-rpl-policy-rule-30)# set as-path prepend last-as 1
	dnRouter(cfg-rpl-policy-rule-30)# exit

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-40)# set as-path prepend last-as 7
	dnRouter(cfg-rpl-policy-rule-40)# exit


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# no set as-path prepend as-number 12956
	dnRouter(cfg-rpl-policy-rule-20)# exit

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-40)# no set as-path prepend


.. **Help line:** Prepend the given string of AS number(s)

**Command History**

+-------------+----------------------------------------------+
|             |                                              |
| Release     | Modification                                 |
+=============+==============================================+
|             |                                              |
| 6.0         | Command introduced                           |
+-------------+----------------------------------------------+
|             |                                              |
| 9.0         | Changed parameter's range from minimum 1     |
+-------------+----------------------------------------------+
|             |                                              |
| 18.2        | Impose action order within route policy rule |
+-------------+----------------------------------------------+