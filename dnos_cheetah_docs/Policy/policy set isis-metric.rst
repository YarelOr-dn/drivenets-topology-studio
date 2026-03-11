policy set isis-metric
----------------------

**Minimum user role:** operator

To set an IS-IS metric value:

**Command syntax: set isis-metric [metric]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- The default metric-type is "internal".

**Parameter table**

+---------------+----------------------------------------------------------+----------------+-------------+
|               |                                                          |                |             |
| Parameter     | Description                                              | Range          | Default     |
+===============+==========================================================+================+=============+
|               |                                                          |                |             |
| metric        | The new value of the IS-IS metric that will be   set.    | 1..16777215    | \-          |
+---------------+----------------------------------------------------------+----------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set isis-metric 20


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set isis-metric


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+