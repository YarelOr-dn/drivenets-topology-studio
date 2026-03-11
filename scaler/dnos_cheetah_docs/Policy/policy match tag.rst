policy match tag
----------------

**Minimum user role:** operator

To match the tag attribute:

**Command syntax: match tag [tag]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+---------------+------------------------+-----------------+-------------+
|               |                        |                 |             |
| Parameter     | Description            | Range           | Default     |
+===============+========================+=================+=============+
| tag           | The tag value to match |                 |             |
|               |                        | 1..4294967295   | \-          |
+---------------+------------------------+-----------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# match tag 55


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no match tag


.. **Help line:** Match the tag attribute

**Command History**

+-------------+--------------------------------------------------+
| Release     | Modification                                     |
+=============+==================================================+
| 6.0         | Command introduced                               |
+-------------+--------------------------------------------------+
| 16.1        | Extended tag range to support unit_32 tag value  |
+-------------+--------------------------------------------------+
