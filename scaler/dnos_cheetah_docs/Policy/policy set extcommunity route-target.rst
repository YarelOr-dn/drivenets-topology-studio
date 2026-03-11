policy set extcommunity route-target
------------------------------------

**Minimum user role:** operator

To set a route-target for the matching routes:

**Command syntax: set extcommunity route-target** additive **[route-target-value]**, [route-target-value],

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- You can set up to 25 different route-targets.

- Within the same route policy rule, "set extcommunity-list" will be processed and imposed before "set extcommunity" action.

**Parameter table**

+-----------------------+----------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
|                       |                                                                      |                                                                                                                                                        | Default |
| Parameter             | Description                                                          | Range                                                                                                                                                  |         |
+=======================+======================================================================+========================================================================================================================================================+=========+
|                       |                                                                      |                                                                                                                                                        | \-      |
| additive              | Appends the route-target to the existing   extcommunities.           | \-                                                                                                                                                     |         |
+-----------------------+----------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
|                       |                                                                      |                                                                                                                                                        | \-      |
| route-target-value    | The route target value to set for matching routes.                   | as-number-short: 0…(2^16 -1)                                                                                                                           |         |
|                       |                                                                      |                                                                                                                                                        |         |
|                       | Type0: <[as-number-short]:[id-long]>                                 | as-number-long: (2^16)…(2^32 -1)                                                                                                                       |         |
|                       |                                                                      |                                                                                                                                                        |         |
|                       | Type1:                                                               | id-short: 0…(2^16 -1)                                                                                                                                  |         |
|                       |                                                                      |                                                                                                                                                        |         |
|                       | <[as-number-short]l: [id-short]>                                     | id-long: 0…(2^32 -1)                                                                                                                                   |         |
|                       |                                                                      |                                                                                                                                                        |         |
|                       | <[as-number-short]L:[id-short]>                                      | ipv4-address-prefix: A.B.C.D                                                                                                                           |         |
|                       |                                                                      |                                                                                                                                                        |         |
|                       | <[as-number-long]:[id-short]>                                        | Note: using [as-number-short]l or [as-number-short]L will code as-number-short number in a 32bit field   resulting in a Type1 route-distinguisher      |         |
|                       |                                                                      |                                                                                                                                                        |         |
|                       | Type2: <[ipv4-address-prefix>:[id-short]>                            |                                                                                                                                                        |         |
|                       |                                                                      |                                                                                                                                                        |         |
|                       | You can set multiple route-target values, separated by a comma       |                                                                                                                                                        |         |
+-----------------------+----------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------+

**Example**

To overwrite the existing extcommunity route-target with new values:
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set extcommunity route-target 65000:1000
	dnRouter(cfg-rpl-policy-rule-10)# exit

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# set extcommunity route-target 65000:1000, 65000:2000
	dnRouter(cfg-rpl-policy-rule-20)# exit


To add values to the existing extcommunity route-target:
::

	dnRouter(cfg-rpl-policy)# rule 30 allow
	dnRouter(cfg-rpl-policy-rule-30)# set extcommunity route-target additive 65000:1000, 65000:2000

**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-30)# no set extcommunity route-target


.. **Help line:** Set a route-target for the matching routes

**Command History**

+-------------+----------------------------+
|             |                            |
| Release     | Modification               |
+=============+============================+
| 6.0         | Command introduced         |
+-------------+----------------------------+
| 11.4        | Added "additive" option    |
+-------------+----------------------------+
| 18.2        | Added note for command     |
|             | restriction                |
+-------------+----------------------------+
| 18.2        | Impose action order within |
|             | route policy rule          |
+-------------+----------------------------+