policy match path-mark-count
----------------------------

**Minimum user role:** operator

To match the number of path-marks over all the route paths:

**Command syntax: match path-mark-count {ge [ge-value] le [le-value] \| eq [le-value]}**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- This command works on routes with a path-mark attribute. See "policy set path-mark".

- The number of path-marks is counted over all BGP paths for a given route, not only on the best paths.

- Use a combination of ge- and le- values to set a range, where le-value is ≥ ge-value.

- The le-value must be greater or equal to the ge-value.

- You cannot set le or ge together with eq.


**Parameter table**

+---------------+------------------------------------------------------------------------+-----------+-------------+
|               |                                                                        |           |             |
| Parameter     | Description                                                            | Range     | Default     |
+===============+========================================================================+===========+=============+
|               |                                                                        |           |             |
| ge-value      | Match to a number that is greater or equal to the   specified value    | 0..32     | \-          |
+---------------+------------------------------------------------------------------------+-----------+-------------+
|               |                                                                        |           |             |
| le-value      | Match to a number that is lower or equal to the specified   value      | 0..32     | \-          |
+---------------+------------------------------------------------------------------------+-----------+-------------+
|               |                                                                        |           |             |
| eq-value      | Match to the specified value                                           | 0..32     | \-          |
+---------------+------------------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy MATCH_PATH_MARK
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# match path-mark-count le 5

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy MATCH_PATH_MARK
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# match path-mark-count ge 1 le 5

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy MATCH_PATH_MARK
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# match path-mark-count eq 3


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)#no match path-mark-count


.. **Help line:** Match to the metric value

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+