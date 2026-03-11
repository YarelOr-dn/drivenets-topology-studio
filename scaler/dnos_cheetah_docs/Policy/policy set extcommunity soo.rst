policy set extcommunity soo
---------------------------

**Minimum user role:** operator

To set a source-of-origin (soo) for the matching routes:

**Command syntax: set extcommunity soo additive [soo-value]**, [soo-value],

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- When setting an extcommunity for Type-1, an L is appended to the AS-number value.

- Within the same route policy rule, "set extcommunity-list" will be processed and imposed before "set extcommunity" action.

- You can set up to 25 different soo-values.


**Parameter table**

+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
|               |                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                        | Default |
| Parameter     | Description                                                                                                                                                                                                                                                                                                                                        | Range                                                                                                                                                  |         |
+===============+====================================================================================================================================================================================================================================================================================================================================================+========================================================================================================================================================+=========+
|               |                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                        | \-      |
| additive      | Appends the route-target to the existing extcommunities.                                                                                                                                                                                                                                                                                           | \-                                                                                                                                                     |         |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
|               |                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                        | \-      |
| soo-value     | BGP site of origin (SoO) is a tag that is appended on BGP updates to allow to mark a specific peer as belonging to a particular site. By tagging the route, BGP will check if the peer's site of origin is listed in the community field. If it is then the route will be filtered. If not, then the route will be advertised as normal.           | as-number-short: 0…(2^16 -1)                                                                                                                           |         |
|               |                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                        |         |
|               | Type0: <[as-number-short]:[id-long]>                                                                                                                                                                                                                                                                                                               | as-number-long: (2^16)…(2^32 -1)                                                                                                                       |         |
|               |                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                        |         |
|               | Type1:                                                                                                                                                                                                                                                                                                                                             | id-short: 0…(2^16 -1)                                                                                                                                  |         |
|               |                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                        |         |
|               | <[as-number-short]l: [id-short]>                                                                                                                                                                                                                                                                                                                   | id-long: 0…(2^32 -1)                                                                                                                                   |         |
|               |                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                        |         |
|               | <[as-number-short]L:[id-short]>                                                                                                                                                                                                                                                                                                                    | ipv4-address-prefix: A.B.C.D                                                                                                                           |         |
|               |                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                        |         |
|               | <[as-number-long]:[id-short]>                                                                                                                                                                                                                                                                                                                      | Note: using [as-number-short]l or [as-number-short]L will code as-number-short number in a 32bit field resulting in a Type1 route-distinguisher        |         |
|               |                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                        |         |
|               | Type2: <[ipv4-address-prefix>:[id-short]>                                                                                                                                                                                                                                                                                                          |                                                                                                                                                        |         |
|               |                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                        |         |
|               | You can set multiple soo values, separated by a comma                                                                                                                                                                                                                                                                                              |                                                                                                                                                        |         |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------+

**Example**

To overwrite the existing extcommunity soo with new values:
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set extcommunity soo 10:1100
	dnRouter(cfg-rpl-policy-rule-10)# exit

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# set extcommunity soo 10:1100, 40:2300
	dnRouter(cfg-rpl-policy-rule-20)# exit


To add values to the existing extcommunity soo:
::

	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set extcommunity soo additive 10:1100, 100:100

**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set extcommunity soo


.. **Help line:** Set a source-of-origin (soo) for the matching routes

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