set interfaces led-flash
------------------------

**Minimum user role:** viewer

When working with a large setup with many interfaces, you may need help in locating the interface that you are configuring in the physical rack. Setting led-flash will cause the LED on the physical port to light.

To enable the LED flash on a physical port:


**Command syntax: set interfaces led-flash [interface-name]**

**Command mode:** operational

**Note**

- The command is applicable to physical interfaces.


**Parameter table**

+-------------------+------------------------------------------------------------------------------+---------------------------------+
|                   |                                                                              |                                 |
| Parameter         | Description                                                                  | Range                           |
+===================+==============================================================================+=================================+
|                   |                                                                              |                                 |
| interface-name    | Specify the name of the physical interface whose   LED you want lit.         | ge<interface speed>-<A>/<B>/<C> |
|                   |                                                                              |                                 |
|                   | If you do not specify an interface, all cluster   interfaces will be lit.    | fab-ncpX-Y/Z/W                  |
|                   |                                                                              |                                 |
|                   |                                                                              | fab-ncfX-Y/Z/W                  |
+-------------------+------------------------------------------------------------------------------+---------------------------------+

**Example**
::

	dnRouter# set interfaces led-flash ge100-1/0/2


**Removing Configuration**

To turn off the LEDs lit by led-flash:
::

	dnRouter# unset interfaces led-flash ge100-1/0/2


.. **Help line:** interfaces led-flash

**Command History**

+-------------+------------------------------------------------+
|             |                                                |
| Release     | Modification                                   |
+=============+================================================+
|             |                                                |
| 6.0         | Command introduced                             |
+-------------+------------------------------------------------+
|             |                                                |
| 7.0         | Moved command from request mode to set mode    |
+-------------+------------------------------------------------+
|             |                                                |
| 9.0         | Command not supported                          |
+-------------+------------------------------------------------+
|             |                                                |
| 11.2        | Command reintroduced                           |
+-------------+------------------------------------------------+