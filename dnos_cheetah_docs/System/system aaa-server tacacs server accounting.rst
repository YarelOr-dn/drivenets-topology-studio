system aaa-server tacacs server priority address accounting
-----------------------------------------------------------

**Minimum user role:** operator

Use this command to enable/disable accounting on the TACACS+ server. When accounting is explicitly enabled and accounting is unavailable, the server will move to the hold-down state. If accounting is disabled, the availability of the remote accounting will not affect the hold-time state considerations.

To configure the admin-state of accounting using the TACACS server:


**Command syntax: accounting [admin-state]**

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
| admin-state | Enable/disable accounting on this server. If enabled, accounting requests may be | | enabled    | disabled |
|             | sent to this server. If disabled, accounting requests will not be sent to this   | | disabled   |          |
|             | server. If no TACACS server is enabled for accounting, only local accounting     |              |          |
|             | will be used; no fallback for authorization/authontication will be used for user |              |          |
|             | login.                                                                           |              |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# server priority 1 address 1.1.1.1
    dnRouter(cfg-aaa-tacacs-server)# accounting enabled


**Removing Configuration**

To revert the admin-state to the default:
::

    dnRouter(cfg-aaa-tacacs-server)# no accounting

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
