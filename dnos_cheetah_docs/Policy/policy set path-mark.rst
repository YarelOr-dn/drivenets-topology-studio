policy set path-mark
--------------------

**Minimum user role:** operator

This command adds a DNOS internal "path-mark" attribute to the route. This provides a means for the BGP ingress policy to count the number of peers from which a certain prefix is learned, regardless of whether or not it is the best path. This information can then be used to take action on the egress routing policy (e.g. change the local preference attribute when a prefix is learned from more than a specific number of peers (see "policy match path-mark-count") so that when the number drops below this value, due to link failure or for any other reason, the egress policy would change the local preference attribute). This capability is useful to allow downstream BGP peers to decide what next-hop to use.

The path-mark attribute is not advertised in BGP.

The path-mark attributes is per prefix. When set as an ingress policy from multiple BGP neighbors, multiple path-marks will be set.

To add the path-mark attribute:


**Command syntax: set path-mark**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- To view the path-mark attribute, use the "show bgp" commands.


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set path-mark


**Removing Configuration**

To remove the set entry for the rule:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set path-mark


.. **Help line:** alert about route aggregation

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+