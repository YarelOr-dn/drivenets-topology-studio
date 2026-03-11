set clock lockout
-----------------

**Minimum user role:** admin

Support set/unset lockout of one of the clock reference source interfaces.

It is possible to temporarily remove a timing source as available synchronization source for the selection process. This is controlled by the lockout commands.

Lockout commands are accepted for synchronization sources that are not disabled of each selection process.

NOTE: A locked out source is still nominated to the selection process and retains its synchronization source priority but no longer considered available for selection.

The unset lockout command causes this input to be considered available again by the selection process.

When performing a clock lockout, you will be prompted to confirm the request. After the request is confirmed, the system will perform the change.

In case the source is already locked-out or the interface is not part of defined input sources, the command should not take any affect.

To set a clock reference source as locked-out:

**Command syntax: set clock lockout {ncp [ncp-id]} interface [interface-name]**

**Command mode:** operational

**Note**

- This command is only applicable to NCP nodes.


**Parameter table**

+------------------+----------------------------------------------------------------------+---------------------------------+
|                  |                                                                      |                                 |
| Parameter        | Description                                                          | Range                           |
+==================+======================================================================+=================================+
| ncp-id           | The unique id of the node whose ref. source you want locked out.     | NCP: 0..191                     |
+------------------+----------------------------------------------------------------------+---------------------------------+
| interface-name   | Reference source interface name                                      | ge<interface speed>-<A>/<B>/<C> |
|                  |                                                                      | smb-10mhz                       |
+------------------+----------------------------------------------------------------------+---------------------------------+

**Example**
::

	dnRouter# set clock lockout ncp 0 interface ge400-0/0/0

	dnRouter# set clock lockout ncp 0 interface smb-10mhz

	dnRouter# set clock lockout ncp 0 interface ge400-0/0/1
	ERROR: Unknown word: 'ge400-0/0/1'.

**Removing Configuration**

To clear the interface lockout state:
::

	dnRouter# unset clock lockout ncp 0 interface ge400-0/0/0

.. **Help line:** clock reference source lockout and clear command support

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 17.2        | Command introduced    |
+-------------+-----------------------+