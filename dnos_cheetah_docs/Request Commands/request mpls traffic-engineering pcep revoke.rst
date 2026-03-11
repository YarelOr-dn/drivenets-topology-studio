request mpls traffic-engineering pcep revoke
--------------------------------------------

**Minimum user role:** operator

To manually revoke delegation from tunnels:

**Command syntax: request mpls traffic-engineering pcep revoke** tunnel [tunnel-name]

**Command mode:** operational

**Note**

- This is a non-persistent change

- The "revoke" command for a tunnel that is not configured with delegation will stop the operational delegation.

**Parameter table**

+--------------+---------------------------------------------------------------+--------+
| Parameter    | Description                                                   | Range  |
+==============+===============================================================+========+
| No parameter | All tunnel delegations will be revoked.                       | \-     |
+--------------+---------------------------------------------------------------+--------+
| tunnel-name  | The delegation will be revoked from the specified tunnel only | String |
+--------------+---------------------------------------------------------------+--------+

**Example**
::

	dnRouter# request mpls-traffic-engineering pcep revoke 
	
	dnRouter# request mpls-traffic-engineering pcep revoke tunnel TUNNEL_A

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+