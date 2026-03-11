system high-availability policy ncc container
---------------------------------------------

**Minimum user role:** operator

Define high-availability policy behavior for software components that reside in the DNOS NCC container.
To enter the container configuration level:

**Command syntax: container [container-name]**

**Command mode:** config

**Hierarchies**

- high-availability policy ncc

**Parameter table:**

+----------------+--------------------------------------------------------------+---------------+
| Parameter      | Values                                                       | Default value |
+================+==============================================================+===============+
| container-name | routing-engine                                               |               |
+----------------+--------------------------------------------------------------+---------------+


.. **Note**


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# high-availability
	dnRouter(cfg-system-ha)# policy
    dnRouter(cfg-system-ha-policy)# ncc
    dnRouter(cfg-ha-policy-ncc)# container routing-engine
    dnRouter(cfg-policy-ncc-container)#



**Removing Configuration**

To revert all container high-availability policy configuration to default values:
::

	dnRouter(cfg-ha-policy-ncc)# no container routing-engine


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
