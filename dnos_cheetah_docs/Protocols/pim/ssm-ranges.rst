protocols pim ssm-ranges
------------------------

**Minimum user role:** operator

Use the following command to configure the PIM-SSM group ranges:

**Command syntax: ssm-ranges [range-policy-prefix-list]**

**Command mode:** config

**Hierarchies**

- protocols pim

**Note**
- PIM register and MSDP SA messages are not accepted, generated, or forwarded for group addresses within the SSM range, unless asm-override is enabled and SSM group sub-ranges are mapped to RPs.

**Parameter table**

+--------------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter                | Description                                                                      | Range            | Default |
+==========================+==================================================================================+==================+=========+
| range-policy-prefix-list | The prefix-list name which uniquely identify a policy that contains one or more  | | string         | \-      |
|                          | policy rules used to accept or reject certain multicast groups. The groups       | | length 1-255   |         |
|                          | accepted by this policy define the multicast group rang used by SSM. If a policy |                  |         |
|                          | is not specified, the default SSM multicast group rang is used. The default SSM  |                  |         |
|                          | multicast group range is 232.0.0.0/8 for IPv4                                    |                  |         |
+--------------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# ssm-ranges SSM-Ranges-Pref-List


**Removing Configuration**

To revert PIM maximum-mfib-routes to default value:
::

    dnRouter(cfg-protocols-pim)# no ssm-ranges

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
