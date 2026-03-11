policy match path-type
----------------------

**Minimum user role:** operator

**Description:** To match BGP routes by path-type, i.e., if the route is learned via iBGP or eBGP:

**Command syntax: match path-type {ebgp | ibgp}**

**Command mode:** config

**Hierarchies**

- routing-policy policy match path-type

.. **Note**


**Parameter table**

+-----------+--------------------------------------------+-------+---------+
| Parameter | Description                                | Range | Default |
+===========+============================================+=======+=========+
| ebgp      | Match the paths that are learned via eBGP. | \-    | \-      |
+-----------+--------------------------------------------+-------+---------+
| ibgp      | Match the paths that are learned via iBGP. | \-    | \-      |
+-----------+--------------------------------------------+-------+---------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# match path-type ibgp


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no match path-type


.. **Help line:** Match the route path type

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.2        | Command introduced    |
+-------------+-----------------------+
