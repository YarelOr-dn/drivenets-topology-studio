system ntp server admin-state
-----------------------------

**Minimum user role:** operator

To configure the remote NTP server admin state.

**Command syntax: admin-state [admin-state]**

**Command mode:** configuration

**Hierarchies**

- system ntp


**Note**

- The commit fails if the NTP server's admin-state is enabled on more than one VRF.

- You can configure up to 5 NTP remote servers with the admin-state enabled on all VRFs.

.. internal notes not relevant to the user

**Parameter table**

+-------------+------------------------------------------------+----------+----------+
| Parameter   | Description                                    | Range    | Default  |
+=============+================================================+==========+==========+
| admin-state | Enable/disable NTP server admin-state.         | Enabled  | Enabled  |
|             |                                                | Disabled |          |
+-------------+------------------------------------------------+----------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)# server 200.24.34.1 vrf default
    dnRouter(cfg-system-ntp-server)# admin-state enabled

    dnRouter(cfg-system-ntp)# server 2001:ab12::1 vrf mgmt0
    dnRouter(cfg-system-ntp-server)# admin-state disabled

**Removing Configuration**

To revert the admin-state to the default value:
::

    dnRouter(cfg-system-ntp-server)# no admin-state



.. **Help line:** Configure system ntp server admin-state


**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.2      | Command introduced    |
+-----------+-----------------------+
