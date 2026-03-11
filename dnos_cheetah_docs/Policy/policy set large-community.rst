policy set large-community
---------------------------

**Minimum user role:** operator

Use this command to add or remove large communities for BGP updates. When you enter multiple entries, they are collected as a list. You can add or remove values to/from the list, and you can do this in separate commits.

To set the specified communities' values to BGP updates:


**Command syntax: set large-community {** **[large-community],** [large-community], . | **additive [large-community],** [large-community], . **\| none }**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- You can set up to 25 large-communities or none.

- Within the same route policy rule, "set large-community-list" will be processed and imposed before "set large-community" action.

**Parameter table**

+-----------------+---------------------------------------------------------------------+---------------------------------------------+---------+
|    Parameter    | Description                                                         |                    Range                    | Default |
+=================+=====================================================================+=============================================+=========+
| large-community | The large-community values to set for BGP updates                   | <AS_number:id-1:id-2> :                     | \-      |
|                 |                                                                     | AS_number: 0..4294967295id-1: 0..4294967295 |         |
|                 |                                                                     | id-2: 0..4294967295                         |         |
+-----------------+---------------------------------------------------------------------+---------------------------------------------+---------+
| additive        | Appends the new large-communities to the existing large-communities |                                             | \-      |
+-----------------+---------------------------------------------------------------------+---------------------------------------------+---------+
| none            | Removes the entire large-communities attribute from BGP updates     |                                             | \-      |
+-----------------+---------------------------------------------------------------------+---------------------------------------------+---------+

**Example**

To overwrite the existing route large-communities with new large-communities:
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set large-community 15562:45:29
	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# set large-community 15562:45:29, 15562:45:50

To add new route large-communities to the existing large-communities:
::

	dnRouter(cfg-rpl-policy)# rule 50 allow
	dnRouter(cfg-rpl-policy-rule-50)# set large-community additive 15562:45:29, 15562:45:50

To delete the existing route large-communities (by overwriting them with "none")
::

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-40)# set large-community none

**Removing Configuration**

To remove all set large-communities:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set large-community

.. **Help line:** The specified large communities value is set to BGP updates.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 15.1        | Command introduced    |
+-------------+-----------------------+
| 18.2        | Added note for command|
|             | restriction           |
+-------------+-----------------------+
| 18.2        | Impose action order   |
|             | within route policy   |
|             | rule                  |
+-------------+-----------------------+
