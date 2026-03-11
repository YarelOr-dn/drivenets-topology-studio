system login ipmi user privilege 
--------------------------------

**Minimum user role:** operator

To configure the privilege level for an IPMI user:

**Command syntax: privilege [level]**

**Command mode:** config

**Hierarchies**

- system login ipmi user


**Note**

- To change the privilege level of an administrator, you need an admin or a techsupport role.

- You cannot change the privilege level for "dnroot".

.. - The full list of IPMI commands and the minimum privilege level per each command are specified by Appendix G in IPMIv2.0 specifciation document.

	**Validation:**

	- only user with admin/techsupport role can edit privilege for users with privilege administrator

	- privilege level for "dnroot" user cannot be changed

	- privilege level is a mandatory parameter, commit will fail if user will be created without setting privilege level

**Parameter table**

+-----------+--------------------------------------------------------------------------------+---------------+---------+
| Parameter | Description                                                                    | Range         | Default |
+===========+================================================================================+===============+=========+
| level     | The privilege level for the IPMI user, as defined by the ipmiv2 specification. | callback      | \-      |
|           |                                                                                | user          |         |
|           |                                                                                | operator      |         |
|           |                                                                                | administrator |         |
+-----------+--------------------------------------------------------------------------------+---------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ipmi
	dnRouter(cfg-system-login-ipmi)# user user1
	dnRouter(system-login-ipmi-user1)# privilege USER

	


.. **Help line:** configure privilege level for ipmi user.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+


