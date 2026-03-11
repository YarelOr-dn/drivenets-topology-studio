policy set tag
--------------

**Minimum user role:** operator

To set the tag attribute:

**Command syntax: set tag [tag]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+---------------+-----------------------------------+------------------+-------------+
|               |                                   |                  |             |
| Parameter     | Description                       | Range            | Default     |
+===============+===================================+==================+=============+
|               |                                   |                  |             |
| tag           | Sets a new tag attribute value    | 1..4294967295    | \-          |
+---------------+-----------------------------------+------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)#set tag 10


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)#no set tag


.. **Help line:** Set the tag attribute MED

**Command History**

+-------------+---------------------------------------------------------+
|             |                                                         |
| Release     | Modification                                            |
+=============+=========================================================+
|             |                                                         |
| 6.0         | Command introduced                                      |
+-------------+---------------------------------------------------------+
|             |                                                         |
| 16.1        | Extended the tag range to support unit_32 tag value     |
+-------------+---------------------------------------------------------+
