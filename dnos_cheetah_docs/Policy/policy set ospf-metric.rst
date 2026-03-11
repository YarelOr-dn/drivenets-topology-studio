policy set ospf-metric
----------------------

**Minimum user role:** operator

You can use the following command to set the OSPFv2/OSPFv3 metric value:

**Command syntax: set ospf-metric [metric]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+---------------+---------------------------------------+------------------+-------------+
|               |                                       |                  |             |
| Parameter     | Description                           | Range            | Default     |
+===============+=======================================+==================+=============+
|               |                                       |                  |             |
| metric        | sets the metric value for OSPFv2/3    | 0..4294967295    | \ -         |
+---------------+---------------------------------------+------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy REDISTRIBUTE_INTO_OSPF
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set ospf-metric 33


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set ospf-metric


.. **Help line:** Set OSPFv2 or OSPFv3 metric value

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.6        | Command introduced    |
+-------------+-----------------------+