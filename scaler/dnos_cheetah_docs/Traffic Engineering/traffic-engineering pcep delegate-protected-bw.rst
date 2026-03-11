traffic-engineering pcep delegate-protected-bw
----------------------------------------------

**Minimum user role:** operator

You can configure all bypass tunnels to advertise their protected-bw to the PCE server via APPLICATION BANDWIDTH Object in the PCEP report (object class 5 object type 5). The Protected-bw is the aggregated bandwidth of all primary tunnels protected by a given bypass tunnel.

To configure the bypass tunnels to advertise their protected-bw:


**Command syntax: delegate-protected-bw [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep

**Parameter table**

+----------------+---------------------------------------------+-------------+-------------+
|                |                                             |             |             |
| Parameter      | Description                                 | Range       | Default     |
+================+=============================================+=============+=============+
|                |                                             |             |             |
| admin-state    | The administrative state of the command.    | Enabled     | Disabled    |
|                |                                             |             |             |
|                |                                             | Disabled    |             |
+----------------+---------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# pcep
	dnRouter(cfg-mpls-te-pcep)# delegate-protected-bw enabled

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-protocols-mpls-te)# no delegate-protected-bw


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.2        | Command introduced    |
+-------------+-----------------------+