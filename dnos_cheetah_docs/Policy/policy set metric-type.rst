policy set metric-type
----------------------

**Minimum user role:** operator

You can use the following command to set the metric type for OSPFv2/OSPFv3:

**Command syntax: set metric-type [metric-type]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+----------------+--------------------------------------+-------------------+-------------+
|                |                                      |                   |             |
| Parameter      | Description                          | Range             | Default     |
+================+======================================+===================+=============+
|                |                                      |                   |             |
| metric-type    | sets the metric-type for OSPFv2/3    | type-1, type-2    | \-          |
+----------------+--------------------------------------+-------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy REDISTRIBUTE_INTO_OSPF
	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-10)# set metric-type type-1


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set metric-type


.. **Help line:** Set metric type for OSPFv2/3.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.6        | Command introduced    |
+-------------+-----------------------+