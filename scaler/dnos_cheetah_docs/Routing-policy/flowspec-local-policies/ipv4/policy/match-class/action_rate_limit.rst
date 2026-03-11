routing-policy flowspec-local-policies ipv4 policy match-class action rate-limit
--------------------------------------------------------------------------------

**Minimum user role:** operator

When matchimg to this match-class, configures that the traffic shall be rate-limited.

**Command syntax: action rate-limit [rate-limit]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 policy match-class

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
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# policy policy-1
    dnRouter(cfg-flp-ipv4-pl)# match-class mc-1
    dnRouter(cfg-ipv4-pl-mc)#  action rate-limit 0
    dnRouter(cfg-ipv4-pl-mc)# exit
    dnRouter(cfg-flp-ipv4-pl)


**Removing Configuration**

To remove the action from the policy:
::

    dnRouter(cfg-ipv4-pl-mc)# no action rate-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
