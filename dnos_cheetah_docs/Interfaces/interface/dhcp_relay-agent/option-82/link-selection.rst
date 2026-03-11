interfaces dhcp relay-agent option-82 link-selection
----------------------------------------------------

**Minimum user role:** operator

"To set the DHCP IPv4 relay agent option-82, sub-option 5, link-selection as specified in RFC 3527:"

**Command syntax: link-selection [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent option-82

**Note**

- The default behavior is to add link-selection sub option with option 82.

- The sub-option is added when enabled and when option-82 is required (option-insert enabled).

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | Support option-82 sub option 5 - link-selection to reflect client ingress        | | enabled    | enabled |
|             | interface ipv4 address                                                           | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# option-82
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# link-selection enabled


**Removing Configuration**

To revert link-selection sub-option usage to default state:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# no link-selection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
