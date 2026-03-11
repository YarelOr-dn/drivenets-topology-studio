system high-availability policy
-------------------------------

**Minimum user role:** operator

The High-availability policy configuration controls the system behavior upon software failure.
A user can define a specific behavior per process, for process recovery and actions upon process failure that exceed the planned amount.

To enter the policy configuration level:

**Command syntax: policy**

**Command mode:** config

**Hierarchies**

- high-availability

.. **Note**

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# high-availability
	dnRouter(cfg-system-ha)# policy
    dnRouter(cfg-system-ha-policy)#



**Removing Configuration**

To remove all high-availability policy configuration and return to default policy behavior:
::

	dnRouter(cfg-system-ha)# no policy


.. **Help line:**

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 16.2        | Command introduced    |
+-------------+-----------------------+
