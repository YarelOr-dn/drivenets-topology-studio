policy set extcommunity color
-----------------------------

**Minimum user role:** operator

To set a color extcommunity for the matching routes:

**Command syntax: set extcommunity color** additive **[color-value]**, [soo-value], ...

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- By default, set will replace any existing extcommunity color value. Use additive to append the extcommunities to existing extcommunities values

- Within the same route policy rule, "set extcommunity-list" will be processed and imposed before "set extcommunity" action

- You can set up to 25 different color-values.


**Parameter table**

+---------------+----------------------------------------------------------+----------------+-------------+
|               |                                                          |                |             |
| Parameter     | Description                                              | Range          | Default     |
+===============+==========================================================+================+=============+
|               |                                                          |                |             |
| color-value   | Color extcommunity value                                 | 0..4294967295  | \-          |
+---------------+----------------------------------------------------------+----------------+-------------+

**Example**

To overwrite the existing extcommunity color with new values:
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set extcommunity color 10
	dnRouter(cfg-rpl-policy-rule-10)# exit

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# set extcommunity color 20, 30
	dnRouter(cfg-rpl-policy-rule-20)# exit


To add values to the existing extcommunity soo:
::

	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set extcommunity color additive 100

**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set extcommunity color


.. **Help line:** Set a color extcommunity for the matching routes

**Command History**

+-------------+----------------------------+
|             |                            |
| Release     | Modification               |
+=============+============================+
|             |                            |
| 17.0        | Command introduced         |
+-------------+----------------------------+
| 18.2        | Impose action order within |
|             | route policy rule          |
+-------------+----------------------------+