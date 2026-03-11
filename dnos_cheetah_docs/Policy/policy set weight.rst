policy set weight
-----------------

**Minimum user role:** operator

To set the route’s BGP route weight attribute:

**Command syntax: set weight [weight]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+---------------+------------------------------------------------------------------+------------------+-------------+
|               |                                                                  |                  |             |
| Parameter     | Description                                                      | Range            | Default     |
+===============+==================================================================+==================+=============+
|               |                                                                  |                  |             |
| weight        | sets a new weight for the BGP route for best path   selection    | 0..4294967295    | \-          |
+---------------+------------------------------------------------------------------+------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set weight 100


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set weight


.. **Help line:** Set the route's weight

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+