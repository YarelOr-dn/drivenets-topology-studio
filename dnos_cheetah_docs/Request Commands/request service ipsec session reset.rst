request service ipsec session reset
-----------------------------------

**Minimum user role:** operator

Resets an IPSec session, with the following granularity: all sessions, all sessions on vrf, a specific device-id session on a specific vrf.

**Command syntax: request service ipsec session reset**  [vrf-name] [device-id]

**Command mode:** operational

**Parameter table**

+--------------+-------------------------------------------------------------+----------------------------+
| Parameter    | Description                                                 | Range                      |
+==============+=============================================================+============================+
| No parameter | This will cause reset for all IPSec sessions                | \-                         |
+--------------+-------------------------------------------------------------+----------------------------+
| vrf-name     | This will cause reset of all IPSec sessions on vrf          | string length 1..255       |
+--------------+-------------------------------------------------------------+----------------------------+
| device-id    | This will cause reset of a specific device-id session       | Device OUI number          |
+--------------+-------------------------------------------------------------+----------------------------+


**Example**
::

	dnRouter# request service ipsec session reset 5e29a47a-cf3b-4b84-9133-71e02f619ec0 DeviceNOUYI_0/384902

	dnRouter# request service ipsec session reset  5e29a47a-cf3b-4b84-9133-71e02f619ec0

	dnRouter# request service ipsec session reset


.. **Help line:** Resets IPSec session/s

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 18.2        | Command introduced    |
+-------------+-----------------------+
