ldp address-family label allocation-filter
------------------------------------------

**Minimum user role:** operator

To configure filtering policies (using an existing IP prefix-list) for selective local label binding:

**Command syntax: label allocation-filter [ipv4-prefix-list-name]**

**Command mode:** config

**Hierarchies**

- protocols ldp address-family

.. **Note**

.. - prefix-list-name type must match address family type

.. - can set a single prefix-list policy

.. - 'no' command removes the label allocation policy

**Parameter table**

+------------------+-------------------------------------------------------------------------+-------------------+---------+
| Parameter        | Description                                                             | Range             | Default |
+==================+=========================================================================+===================+=========+
| prefix-list-name | The name of the configured prefix list. See routing-policy prefix-list. | 1..255 characters | \-      |
+------------------+-------------------------------------------------------------------------+-------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# label allocation-filter PL4_LDP_FILTER

**Removing Configuration**

To remove all prefix list policies:
::

	dnRouter(cfg-protocols-ldp-afi)# no label allocation-filter

.. **Help line:** Enables the configuration of filtering policies for selective local label binding

**Command History**

+-------------+-------------------------------------------------------------------+
|             |                                                                   |
| Release     | Modification                                                      |
+=============+===================================================================+
|             |                                                                   |
| 6.0         | Command introduced                                                |
+-------------+-------------------------------------------------------------------+
|             |                                                                   |
| 13.0        | Command syntax changed from allocated-for to allocation-filter    |
+-------------+-------------------------------------------------------------------+