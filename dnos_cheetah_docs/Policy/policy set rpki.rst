policy set rpki
---------------

**Minimum user role:** operator

To set the RPKI state in announcements enabled towards iBGP peers:

**Command syntax: set rpki [rpki-state]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- The rpki state will affect BGP neighbors for which announce rpki-state is set and as long as extended community is enabled.

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
	dnRouter(cfg-rpl-policy-rule-10)#set rpki not-found


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set rpki


.. **Help line:** Set the RPKI state

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.1        | Command introduced    |
+-------------+-----------------------+