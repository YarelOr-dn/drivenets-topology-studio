request segment-routing pcep delegate peer
------------------------------------------

**Minimum user role:** operator

The command allows you to manually delegate all sr-te policies to the stated PCE peer.
This applies for policies that are not configured with delegation enabled as well.
The request is non-persistent. When the PCEP session with the requested PCE server is closed, the delegation will return to the normal behavior, according to the configuration.

If the policy's state changes to down, the policy maintains the operational delegation to the requested PCE.

To manually delegate policies to a specific PCE peer:

**Command syntax: request segment-routing pcep delegate peer [ipv4-address]**

**Command mode:** operational

**Note**

- Changing the policy delegation configuration from enabled to disabled will also remove the delegation that was set due to the request command.

- The request delegation affects all policies. New policies that are configured with delegation will be delegated to the request PCE server and not according to the configuration.


**Parameter table**

+--------------+-------------------------------------------------------------+---------+
| Parameter    | Description                                                 | Range   |
+==============+=============================================================+=========+
| ipv4-address | The system will delegate all tunnels to the specified peer  | A.B.C.D |
+--------------+-------------------------------------------------------------+---------+

**Example**
::

	dnRouter# request segment-routing pcep delegate peer 1.1.1.1


.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
