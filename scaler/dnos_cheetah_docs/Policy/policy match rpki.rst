policy match rpki
-----------------

**Minimum user role:** operator

To match advertised prefixes on RPKI state:

**Command syntax: match rpki [rpki-state]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+---------------+-------------------------------+--------------+-------------+
|               |                               |              |             |
| Parameter     | Description                   | Range        | Default     |
+===============+===============================+==============+=============+
|               |                               |              |             |
| rpki-state    | The rpki validation state     | Valid        | \-          |
|               |                               |              |             |
|               |                               | Invalid      |             |
|               |                               |              |             |
|               |                               | Not-found    |             |
+---------------+-------------------------------+--------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# match rpki valid


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no match rpki


.. **Help line:** Match advertised prefixes on RPKI state

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.1        | Command introduced    |
+-------------+-----------------------+