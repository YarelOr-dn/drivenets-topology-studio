system high-availability policy ncc container process
-----------------------------------------------------

**Minimum user role:** operator

Defines the high-availability policy behavior for processes residing in the DNOS NCC container.
To enter the process configuration level:

**Command syntax: process [process-name]**

**Command mode:** config

**Hierarchies**

- high-availability policy ncc container

**Parameter table:**

+----------------+--------------------------------------------------------------+---------------+
| Parameter      | Values                                                       | Default value |
+================+==============================================================+===============+
| process-name   | See DNOS High-Availablity guide for configurable processes   |  \-           |
+----------------+--------------------------------------------------------------+---------------+


**Note**


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# high-availability
	dnRouter(cfg-system-ha)# policy
    dnRouter(cfg-system-ha-policy)# ncc
    dnRouter(cfg-ha-policy-ncc)# container routing-engine
    dnRouter(cfg-policy-ncc-container)# process routing:pimd
    dnRouter(cfg-ncc-container-process)#



**Removing Configuration**

To revert all process high-availability policy configuration to default values:
::

	dnRouter(cfg-policy-ncc-container)# no process routing:pimd


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
