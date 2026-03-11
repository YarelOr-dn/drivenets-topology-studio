policy set local-preference
---------------------------

**Minimum user role:** operator

Routers in the same AS exchange the local preference attribute in order to indicate to the AS which path is preferred for exiting the AS and reaching a specific network. A path with a higher local preference is preferred more. 

To set a preference value for the BGP local preference:

**Command syntax: set local-preference [metric]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+---------------------------+--------------------------------------+------------------+-------------+
|                           |                                      |                  |             |
| Parameter                 | Description                          | Range            | Default     |
+===========================+======================================+==================+=============+
|                           |                                      |                  |             |
| local-preference-value    | sets a new local preference value    | 0..4294967295    | \-          |
+---------------------------+--------------------------------------+------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-20)#set local-preference 90


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set local-preference


.. **Help line:** Set a preference value for the as path

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+