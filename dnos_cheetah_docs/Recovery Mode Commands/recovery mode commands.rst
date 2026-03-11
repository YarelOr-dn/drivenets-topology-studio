Recovery Mode Commands
----------------------

**Minimum user role:** techsupport

When you log in to a system in recovery mode, a banner indicating that the system is in recovery mode is displayed:

When the system is in recovery mode, the following commands are available:

+---------------------------------+----------------------------------------+
| Command                         | Reference                              |
+=================================+========================================+
| request system restart          | request system restart                 |
+---------------------------------+----------------------------------------+
| request system factory-default  | request system restart factory-default |
+---------------------------------+----------------------------------------+
| request system restart rollback | request system restart rollback        |
+---------------------------------+----------------------------------------+
| request system tech-support     | request system tech-support            |
+---------------------------------+----------------------------------------+
| show rollback                   | show rollback                          |
+---------------------------------+----------------------------------------+
| run start shell                 | run start shell                        |
+---------------------------------+----------------------------------------+

**Command mode:** recovery

**Note**

- These commands are not logged or accounted by TACACS.

- You have a single attempt to enter a valid password.

.. - User will have a single attempt to enter password

**Example**
::

	user@user-1:~/HOME$ ssh 0 -p 2223 -l dnroot
	System is in Recovery mode!
	dnroot@0's password:



