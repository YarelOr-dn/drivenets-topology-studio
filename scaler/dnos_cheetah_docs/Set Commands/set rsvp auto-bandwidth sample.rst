set rsvp auto-bandwidth sample
----------------------------------

**Minimum user role:** operator

Manually set the average-traffic-rate value, which is sampled by the tunnel on every auto-bandwidth sampling-interval. Upon the requested sampled value all auto-bandwidth logic will apply. The tunnel for which average-traffic-rate sample will be modified can be specified. The sampled average-traffic-rate will remain the requested value until running the "unset rsvp auto-bandwidth sample" command or until the rsvp process restarts.

To set the rsvp auto-bandwidth tunnel:

**Command syntax: set rsvp auto-bandwidth sample tunnel [tunnel-name] bandwidth [bandwidth]**

**Command mode:** operational

**Parameter table**

+-------------+----------------------------------+---------------+
| Parameter   | Description                      | Range         |
+=============+==================================+===============+
| tunnel-name | The name of the specific tunnel  | string        |
+-------------+----------------------------------+---------------+
| bandwidth   | The set bandwidth for the tunnel | 0..4294967295 |
+-------------+----------------------------------+---------------+

**Example**
::

	dnRouter# set rsvp auto-bandwidth sample tunnel TUNNEL_A bandwidth 500000


**Removing Configuration**

To clear the average-rate traffic for all tunnels:
::

	dnRouter# unset rsvp auto-bandwidth sample

To clear the average-rate traffic for a specific tunnel:
::

	dnRouter# unset rsvp auto-bandwidth sample tunnel TUNNEL_A

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.2        | Command introduced    |
+-------------+-----------------------+
