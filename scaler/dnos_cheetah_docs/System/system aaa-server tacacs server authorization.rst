system aaa-server tacacs server priority address authorization
--------------------------------------------------------------

**Minimum user role:** operator

To configure the admin state of authorization using the TACACS server:

**Command syntax: authorization [admin-state]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs server priority address

**Note**
- Notice the change in prompt.

.. - 'no' command sets default admin-state value.


**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Enable/disable authorization on this server. If enabled, authorization requests  | | enabled    | disabled |
|             | may be sent to this server. If disabled, authorization requests will not be sent | | disabled   |          |
|             | to this server. If no TACACS server is enabled for authorization, local users    |              |          |
|             | will be used for login.                                                          |              |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# server priority 1 address 1.1.1.1
    dnRouter(cfg-aaa-tacacs-server)# authorization enabled


**Removing Configuration**

To revert authorization to default:
::

    dnRouter(cfg-aaa-tacacs-server)# no authorization

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
