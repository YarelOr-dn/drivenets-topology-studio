show system login users
-----------------------

**Minimum user role:** viewer

The following command displays a list of the locally configured users.

Failed logins present the number of failures due to wrong credentials. When the number of failed logins reaches the configured velue (system login session-retry), the user is blocked for a specific time (system login session-holdoff)

**Command syntax: show system login users**

**Command mode:** operational



**Note**

- Local users are not available when TACACS+ authentication is configured.

.. - local users are not available when TACACS authentication is set

	- Failed logins present number of wrong credentials login attmempts. When number of failed logins reaches the configured value (system login session-retry), user is blocked for specific time (system login session-holdoff). 

	- Hold-off presents amount of time until user will be locked out. After hold-off time reach 0:00, user is locked out and "Failed Logins" value is set to 0.

	- Hold-off time is presented only of locked users

**Parameter table**

+-------------+---------------------------------------+-------------+---------+
| Parameter   | Description                           | Range       | Default |
+=============+=======================================+=============+=========+
| user        | The name of user                      | string      | \-      |
+-------------+---------------------------------------+-------------+---------+
| role        | The user role                         | Admin       |         |
|             |                                       | Techsupport | \-      |
|             |                                       | Viewer      |         |
|             |                                       | Operator    |         |
+-------------+---------------------------------------+-------------+---------+
| Description | The description provided for the user | string      | \-      |
+-------------+---------------------------------------+-------------+---------+

**Example**
::

	dnRouter# show system login users
	
	Locally Configured:
	| User   | Role      | Failed Logins | Hold-off  | Description   |
	|--------+-----------+---------------+-----------+---------------|
	| dnroot | Admin     | 2             |           |               |
	| john   | Operator  | 0             |           |               |
	| steve  | Viewer    | 8             | 00:09:59  |               |
	
	

.. **Help line:** show list of local users

**Command History**

+---------+------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                         |
+=========+======================================================================================================+
| 5.1.0   | Command introduced                                                                                   |
+---------+------------------------------------------------------------------------------------------------------+
| 6.0     | Updated the command show system users to show system login users and example to include strict users |
+---------+------------------------------------------------------------------------------------------------------+
| 10.0    | Removed strict user support.                                                                         |
+---------+------------------------------------------------------------------------------------------------------+

