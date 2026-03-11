routing-policy flowspec-local-policies ipv6 policy match-class action rate-limit
--------------------------------------------------------------------------------

**Minimum user role:** operator

When matching to this match-class, configures that the traffic shall be rate-limited.

**Command syntax: action rate-limit [rate-limit]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv6 policy match-class

**Parameter table**

+------------+------------------------------------------------------+------------------+---------+
| Parameter  | Description                                          | Range            | Default |
+============+======================================================+==================+=========+
| rate-limit | The rate in kbits per second to limit the traffic to | 0, 64-4294967295 | \-      |
+------------+------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# policy policy-1
    dnRouter(cfg-flp-ipv6-pl)# match-class mc-1
    dnRouter(cfg-ipv6-pl-mc)#  action rate-limit 0
    dnRouter(cfg-ipv6-pl-mc)# exit
    dnRouter(cfg-flp-ipv6-pl)


**Removing Configuration**

To remove the action from the policy:
::

    dnRouter(cfg-ipv6-pl-mc)# no action rate-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
