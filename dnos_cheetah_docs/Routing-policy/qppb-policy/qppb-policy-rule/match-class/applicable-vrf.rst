routing-policy qppb-policy rule match-class applicable-vrf
----------------------------------------------------------

**Minimum user role:** operator

To Configure the VRF that the rule shall be applied to.

**Command syntax: applicable-vrf [applicable-vrf]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule match-class

**Parameter table**

+----------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                                      | Range            | Default |
+================+==================================================================================+==================+=========+
| applicable-vrf | applicable vrf defines the vrf to which the src-class and dest-class are         | | string         | default |
|                | applicable                                                                       | | length 1-255   |         |
+----------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# match-class
    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class) applicable-vrf VRF-1
    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class)


**Removing Configuration**

To restore the applicable-vrf back to its default value - to the default VRF
::

    dnRouter(fg-qppb-policy-PL-1-rule-10-match-class)# no applicable-vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
