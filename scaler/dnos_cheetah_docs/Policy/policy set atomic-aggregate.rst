policy set atomic-aggregate
---------------------------

**Minimum user role:** operator

When applied, BGP speakers alert BGP speakers along the path that some information has been lost due to the route aggregation process and that the aggregate path might not be the best path to the destination.

To add atomic-aggregate attribute to the BGP update:

**Command syntax: set atomic-aggregate**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set atomic-aggregate


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set atomic-aggregate


.. **Help line:** alert about route aggregation

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+