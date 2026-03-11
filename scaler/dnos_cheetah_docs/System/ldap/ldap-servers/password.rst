system ldap ldap-server priority password
-----------------------------------------

**Minimum user role:** admin

Enables configuring a password for the LDAP server. The password must match the password configured on the LDAP server. You can enter the password in plain-text, but it will be displayed in an encrypted form with an enc- prefix in any show command. The encryption is performed with the same key used by the system to decrypt the password during load/copy of the configuration. If you do not enter a password, you will be prompted for the (unencrypted) password. To define a password for the remote LDAP server:

**Command syntax: password [password]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-server priority

**Note**
- Notice the change in prompt.

- You will not be able to commit the configuration without a configured password.

.. -  Password configuration is mandatory for radius server (clear or encrypted):

   -  password can made up of ASCII alphanumeric characters ([A-Za-z0-9])

   -  password must be between 1 to 64 character

   -  at least 1 alphabet character must be configured

   -  if password is not configured, commit will fail

   -  password cannot be removed


**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| password  | The admin/root password, supplied as a hashed value using the notation described | \-    | \-      |
|           | in the definition of the crypt-password-type.                                    |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-server priority 1
    dnRouter(cfg-system-ldap-server)# password
    Enter password
    Enter password for verifications


**Removing Configuration**

Once configured, the password cannot be deleted, only changed.
::

    dnRouter(cfg-system-ldap-server)# no password

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
