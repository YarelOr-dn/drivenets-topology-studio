request rsvp auto-bandwidth adjust
----------------------------------

**Minimum user role:** operator

To manually perform auto-bandwidth adjustments:

**Command syntax: request rsvp auto-bandwidth adjust** tunnel [tunnel-name] bandwidth [bandwidth]

**Command mode:** operational

**Note**

- The general command (request rsvp auto-bandwidth adjust) performs adjustments to all tunnels with auto-bandwidth enabled. The adjustments are made based on the current adjustment interval and maximum average traffic rate. The action will reset the relevant adjust timer and adjust-threshold. See "rsvp auto-bandwidth for details".

**Parameter table**

+-------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Parameter   | Description                                                                                                                                                                                   | Range                    |
+=============+===============================================================================================================================================================================================+==========================+
| tunnel-name | Manually performs auto-bandwidth adjustments to the specified tunnel only.                                                                                                                    | String 1..255 characters |
+-------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| bandwidth   | Manually perform auto-bandwidth adjustment with the specified bandwidth value as the average traffic rate. The specified bandwidth value is compared to the tunnel auto-bandwidth thresholds. | 0..4294967295 kbps       |
+-------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+

**Example**
::

	dnRouter# request rsvp auto-bandwidth adjust
	dnRouter# request rsvp auto-bandwidth adjust tunnel TUNNEL_A
	dnRouter# request rsvp auto-bandwidth adjust bandwidth 500000
	dnRouter# request rsvp auto-bandwidth adjust tunnel TUNNEL_A bandwidth 500000 

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+