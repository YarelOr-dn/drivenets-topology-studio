qos mib-enable
-------------------

**Minimum user role:** operator

The QoS MIB describes the names and optional description strings of policies, rules and traffic classes, and how the three are combined together. The MIB models the hierarchy between configuration objects (not instances). This has two advantages: it allows the QoS hierarchy to be queried even if no policy is provisioned (attached to an interface), and it ensures that the hierarchy table scale does not increase linearly with the number of provisioned interfaces, therefore requiring less resources for querying all tables when the number of interfaces is large.

To enable QoS telemetry via SNMP:

**Command syntax: qos mib [mib-enable]**

**Command mode:** config

**Hierarchies**

- qos

**Parameter table**

+---------------+---------------------------------------------+-------------+-------------+
|               |                                             |             |             |
| Parameter     | Description                                 | Range       | Default     |
+===============+=============================================+=============+=============+
|               |                                             |             |             |
| mib-enable    | To enable/disable QoS telemetry via SNMP    | Enabled     | Disabled    |
|               |                                             |             |             |
|               |                                             | Disabled    |             |
+---------------+---------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# mib enabled


**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-qos)# no mib

.. **Help line:** Enable QoS telemetry via SNMP

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.0        | Command introduced    |
+-------------+-----------------------+
