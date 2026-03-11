request mpls traffic-engineering pcep delegate peer
---------------------------------------------------

**Minimum user role:** operator

Manually delegate all tunnels to the stated peer. This command applies only for LSPs that are configured with delegation enabled.

This request command is non-persistent. When the PCEP session with the requested PCE server is closed, the delegation will return to the normal behavior, according to the configuration, and PCE best priority.

If the tunnel's state changes to down, the tunnel maintains the operational delegation to the requested PCE.

To manually delegate tunnels to a specific PCE peer:

**Command syntax: request mpls-traffic-engineering pcep delegate peer [ipv4-address]**

**Command mode:** operational

**Note**

- Changing the tunnel delegation configuration from enabled to disabled will also remove the delegation that was set due to the request command.

- The request delegation only affects existing tunnels. New tunnels that are configured with delegation will be delegated to the request PCE server and not according to the configuration.


**Parameter table**

+--------------+-------------------------------------------------------------+---------+
| Parameter    | Description                                                 | Range   |
+==============+=============================================================+=========+
| ipv4-address | The system will delegate all tunnels to the specified peer. | A.B.C.D |
+--------------+-------------------------------------------------------------+---------+

**Example**
::

	dnRouter# request mpls traffic-engineering pcep delegate peer 1.1.1.1


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+
