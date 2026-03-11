policy match community
----------------------

**Minimum user role:** operator

To match BGP updates using a community-list:

**Command syntax: match community [community-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+---------------------+------------------------------------+-------------------+---------+
| Parameter           | Description                        | Range             | Default |
+---------------------+------------------------------------+-------------------+---------+
| Community-list-name | The community-list's name to match | 1..255 characters | \-      |
+---------------------+------------------------------------+-------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow

	dnRouter(cfg-rpl-policy-rule-10)#  match community CL_RTBH


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)#  no match community


.. **Help line:** Match by community list

**Command History**

+-------------+-----------------------------------------+
|             |                                         |
| Release     | Modification                            |
+=============+=========================================+
|             |                                         |
| 6.0         | Command introduced                      |
+-------------+-----------------------------------------+
|             |                                         |
| 10.0        | Match is done using a community-list    |
+-------------+-----------------------------------------+
|             |                                         |
| 11.0        | Removed the option for exact-match      |
+-------------+-----------------------------------------+