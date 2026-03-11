set system led-flash
--------------------

**Minimum user role:** viewer

When working with large setups with many elements, you may need help in locating a specific machine. Setting the led-flash will cause all of the port LEDs on the specified element to blink.

To locate a machine using the LED-flash:

**Command syntax: set system led-flash** [node-name] [node-id]

**Command mode:** operational

**Note**

- This command is not applicable to NCC and NCM.

- If you do not specify an NCE, the LEDs of all the cluster's NCP and NCF will blink.

**Parameter table**

+---------------+----------------------------------------------------------------------+---------------+
|               |                                                                      |               |
| Parameter     | Description                                                          | Range         |
+===============+======================================================================+===============+
|               |                                                                      |               |
| node-name     | Specify the NCE whose port LEDs you want lit.                        | NCP           |
|               |                                                                      |               |
|               |                                                                      | NCF           |
+---------------+----------------------------------------------------------------------+---------------+
|               |                                                                      |               |
| node-id       | The unique identifier of the node whose port LEDs   you want lit.    | NCP: 0..191   |
|               |                                                                      |               |
|               |                                                                      | NCF: 0..12    |
+---------------+----------------------------------------------------------------------+---------------+

**Example**
::

	dnRouter# set system led-flash
	dnRouter# set system led-flash ncp 0
	dnRouter# set system led-flash ncf 1

**Removing Configuration**

To stop the blinking on all nodes:
::

	dnRouter# unset system led-flash

To stop the blinking on a specific node:
::

	dnRouter# unset system led-flash ncp 0


.. **Help line:** interface led-flash

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+