request retry-install flowspec-local-policy-rules
--------------------------------------------------

**Minimum user role:** operator

To install any uninstalled Flowspec Local Policy rules:

**Command syntax: request retry-install flowspec-local-policy-rules** {[address-family]}

**Command mode:** operation

.. **Hierarchies**

**Note**

- When the address-family is not provided then the retry-install command will be applied to both the IPv4 and the IPv6 installed rules.

**Parameter table:**


+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                   |                                                                                                                                                     |                     |             |
| Parameter         | Description                                                                                                                                         | Range               | Default     |
+===================+=====================================================================================================================================================+=====================+=============+
|                   |                                                                                                                                                     |                     |             |
| address-family    | Attempts to install any rules that were not yet installed for the specified address-family. When the address-family is not specified,               | IPv4                | both        |
|                   | the command will apply to both IPv4 and IPv6.                                                                                                       |                     |             |
|                   |                                                                                                                                                     | IPv6                |             |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+


**Example**
::

	dnRouter# request retry-install flowspec-local-policy-rules
	dnRouter# request retry-install flowspec-local-policy-rules ipv4
	dnRouter# request retry-install flowspec-local-policy-rules ipv6


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 17.0        | Command introduced    |
+-------------+-----------------------+