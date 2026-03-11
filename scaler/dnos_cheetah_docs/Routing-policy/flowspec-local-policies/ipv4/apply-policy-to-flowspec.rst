routing-policy flowspec-local-policies ipv4 apply-policy-to-flowspec
--------------------------------------------------------------------

**Minimum user role:** operator

Specifys which of the policies that were defined for IPv4, that should be installed - only one policy may be installed.

**Command syntax: apply-policy-to-flowspec [apply-to-flowspec-policy-name]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4

**Parameter table**

+-------------------------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter                     | Description                                                                      | Range  | Default |
+-------------------------------+----------------------------------------------------------------------------------+--------+---------+
| apply-to-flowspec-policy-name | The name of ipv4 policy to install - only a single ipv4 policy may be installed. | string | \-      |
|                               |                                                                                  | length |         |
|                               |                                                                                  | 1..255 |         |
+-------------------------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy-based-routing
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# apply-policy-to-flowspec policy-1
    dnRouter(cfg-rpl-flp-ipv4)#


**Removing Configuration**

To remove the policy that was installed.
::

    dnRouter(cfg-flp-ipv4-mc)# no apply-policy-to-flowspec policy-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
