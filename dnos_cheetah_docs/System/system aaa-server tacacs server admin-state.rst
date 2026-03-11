system aaa-server tacacs server priority address admin-state
------------------------------------------------------------

**Minimum user role:** admin

You can use this command to configure the admin state of remote AAA TACACS server. To enable the TACACS server:


**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs server priority address

**Note**
- Validation: the commit fails if more than one in-band management non-default VRF is configured with an admin-state “enabled” knob.


**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | Configure the admin state of remote AAA. If aaa-server admin-state is enabled,   | | enabled    | enabled |
|             | each AAA request will be sent to one of the AAA servers that are enabled for the | | disabled   |         |
|             | required AAA function. Servers can be separately enabled or disabled for each    |              |         |
|             | one of the three AAA functions.                                                  |              |         |
|             | If no AAA server is enabled for one of the functions, no AAA requests will be    |              |         |
|             | sent at all, and local users will be used for login. If aaa-server admin-state   |              |         |
|             | is disabled, local users will be used for login.                                 |              |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# server priority 1 address 1.1.1.1
    dnRouter(cfg-aaa-tacacs-server)# admin-state enabled


**Removing Configuration**

To revert to the default admin-state:
::

    dnRouter(cfg-aaa-tacacs-server)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
