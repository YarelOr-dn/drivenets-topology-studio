qos policy rule action police meter-type tr3cm color-mode
---------------------------------------------------------

**Minimum user role:** operator

To configure the policer color mode:

**Command syntax: color-mode [color-mode]**

**Command mode:** config

**Hierarchies**

- qos policy rule action police meter-type tr3cm

**Note**

- You can view the policer rate and bucket size parameters in the 'show qos interface' command.

- The policer bucket size that can be set in the hardware is 50 KB, even if the relative settings calculation arrives at a smaller value. The policer's largest size is set to 255 MB, even if the relative calculation is a larger value. The actual settable values are displayed in the 'show qos interfaces' command.

**Parameter table**

+------------+-------------------------------------------------------------------+-----------------+-------------+
| Parameter  | Description                                                       | Range           | Default     |
+============+===================================================================+=================+=============+
| color-mode | Take in-color into account, or treat all matched traffic as green | | color-blind   | color-blind |
|            |                                                                   | | color-aware   |             |
+------------+-------------------------------------------------------------------+-----------------+-------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# police
    dnRouter(cfg-rule-1-action-police)# meter-type tr3ccm
    dnRouter(cfg-action-police-tr3ccm)# color-mode color-aware
    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# police
    dnRouter(cfg-rule-1-action-police)# meter-type tr3cm
    dnRouter(cfg-action-police-tr3cm)# color-mode color-blind
    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# police
    dnRouter(cfg-rule-1-action-police)# meter-type sr3cm
    dnRouter(cfg-action-police-sr3cm)# color-mode color-blind


**Removing Configuration**

To remove color mode:
::

    dnRouter(cfg-action-police-tr3ccm)# no color-mode

**Command History**

+---------+--------------------------------------------------------------+
| Release | Modification                                                 |
+=========+==============================================================+
| 13.1    | Command introduced                                           |
+---------+--------------------------------------------------------------+
| 16.1    | Split from the generic qos-policy-action-police-rate command |
+---------+--------------------------------------------------------------+
