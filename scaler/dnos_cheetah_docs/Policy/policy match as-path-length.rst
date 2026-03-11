policy match as-path-length
---------------------------

**Minimum user role:** operator

To compare the AS numbers in the AS-path of a BGP route:

**Command syntax: match as-path-length [as-path-length-range]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+-------------------------+-------------------------------------+------------------------+------------+
|                         |                                     |                        |            |
| Parameter               | Description                         | Range                  | Default    |
+=========================+=====================================+========================+============+
|                         |                                     |                        |            |
| as-path-length-range    | the number of ASN in the AS-path    | 0..1024 (x-y range)    | \-         |
+-------------------------+-------------------------------------+------------------------+------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# match as-path-length 51-1024
	dnRouter(cfg-rpl-policy-rule-10)# # exit 
	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# match as-path-length 13
	dnRouter(cfg-rpl-policy)# rule 30 allow
	dnRouter(cfg-rpl-policy-rule-30)# match as-path-length 5-10
	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-40)# match as-path-length 0-3

**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no match as-path-length


.. **Help line:** Compare the number of ASN in the as-path

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+