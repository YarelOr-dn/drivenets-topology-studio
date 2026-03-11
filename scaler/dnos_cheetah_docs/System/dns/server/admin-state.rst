system dns server priority ip-address admin-state
-------------------------------------------------

**Minimum user role:** operator

You can use this command to configure the admin state of remote DNS server. To enable the DNS server:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system dns server priority ip-address

**Note**

- Validation: fail commit if more than one in-band management non-default VRF is configured with admin-state “enabled” knob.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | Configure the admin state of remote DNS server. If dns server admin-state is     | | enabled    | enabled |
|             | enabled, each DNS query will be sent to one of the DNS servers that are enabled  | | disabled   |         |
|             | on that VRF according to their priotrity. Servers can be separately enabled or   |              |         |
|             | disabled.                                                                        |              |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# dns
    dnRouter(cfg-system-dns)# server priority 1 ip-address 12.127.17.83 vrf default
    dnRouter(cfg-system-dns-server)# admin-state disabled
    dnRouter(cfg-system-dns-server)# admin-state enabled


**Removing Configuration**

To revert to the default admin-state:
::

    dnRouter(cfg-system-dns-server)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
