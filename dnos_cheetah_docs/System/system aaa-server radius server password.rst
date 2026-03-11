system aaa-server radius server password
----------------------------------------

**Minimum user role:** operator

Configure a password for the RADIUS server.

The password must match the password configured on the AAA server. You can enter the password in plain-text, but it will be displayed in an encrypted form with an enc- prefix in any show command. The encryption is performed with the same key used by the system to decrypt the password during load/copy of configuration.

If you do not enter a password, you will be prompted for the (unencrypted) password.

To define a password for the remote RADIUS server:

**Command syntax: password** [password]

**Command mode:** config

**Hierarchies**

- system aaa-server radius server


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

+-----------+------------------------------------------------------------------------------------------------------------------------------+-------------------------+---------+
| Parameter | Description                                                                                                                  | Range                   | Default |
+===========+==============================================================================================================================+=========================+=========+
| password  | The shared secret between the device and the AAA server that is used to authenticate requests and replies.                   | string 1..64 characters | \-      |
|           | The length of the password must be between 1 and 64 ASCII alphanumeric characters (A-Z, a-z, 0-9), with at least one letter. |                         |         |
+-----------+------------------------------------------------------------------------------------------------------------------------------+-------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# radius
    dnRouter(cfg-system-aaa-radius)# server priority 3 address 192.168.1.3
    dnRouter(cfg-aaa-radius-server)# password enc-!@#$%

    dnRouter(cfg-aaa-radius-server)# password
    Enter password:
    Enter password for verification:


**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-system-aaa-radius)# no server 192.168.1.3


.. **Help line:** Configure RADIUS server password

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+

