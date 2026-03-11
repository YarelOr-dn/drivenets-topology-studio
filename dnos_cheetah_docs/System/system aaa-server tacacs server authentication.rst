system aaa-server tacacs server priority address authentication
---------------------------------------------------------------

**Minimum user role:** operator

To configure the admin state of authentication using the TACACS server:

**Command syntax: authentication [admin-state]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs server priority address

**Note**
- Notice the change in prompt.

.. - 'no authentication' command sets default authentication value


**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Enable/disable authentication on this server. If enabled, authentication         | | enabled    | disabled |
|             | requests may be sent to this server. If disabled, authentication requests will   | | disabled   |          |
|             | not be sent to this server. If no TACACS server is enabled for authentication,   |              |          |
|             | local users will be used for login.                                              |              |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# server priority 1 address 1.1.1.1
    dnRouter(cfg-aaa-tacacs-server)# authentication enabled


**Removing Configuration**

To revert the admin-state to the default:
::

    dnRouter(cfg-aaa-tacacs-server)# no authentication

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
