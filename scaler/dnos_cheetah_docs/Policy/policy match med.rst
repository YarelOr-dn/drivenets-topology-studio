policy match med
----------------

**Minimum user role:** operator

To match to the multi-exit discriminator metric value:

**Command syntax: match med [med]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+--------------+------------------------------------------------+------------------+------------+
|              |                                                |                  |            |
| Parameter    | Description                                    | Range            | Default    |
+==============+================================================+==================+============+
|              |                                                |                  |            |
| med          | the multi-exit discriminator value to match    | 0..4294967295    | \-         |
+--------------+------------------------------------------------+------------------+------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# match med 40000


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)#no match med


.. **Help line:** Match to the metric value

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+