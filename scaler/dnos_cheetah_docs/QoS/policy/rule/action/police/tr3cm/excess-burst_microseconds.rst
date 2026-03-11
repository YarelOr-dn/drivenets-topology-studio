qos policy rule action police meter-type tr3cm excess-burst
-----------------------------------------------------------

**Minimum user role:** operator

To configure the excess-burst rate in milliseconds or microseconds:

**Command syntax: excess-burst [ebs-microseconds] [units]**

**Command mode:** config

**Hierarchies**

- qos policy rule action police meter-type tr3cm

**Note**

- You can view the policer rate and bucket size parameters in the 'show qos interface' command.

- The policer bucket size that can be set in the hardware is 50 KB, even if the relative settings calculation arrives at a smaller value. The policer's largest size is set to 255 MB, even if the relative calculation is a larger value. The actual settable values are displayed in the 'show qos interfaces' command.

**Parameter table**

+------------------+-----------------------------------+------------------+--------------+
| Parameter        | Description                       | Range            | Default      |
+==================+===================================+==================+==============+
| ebs-microseconds | excess burst size in microseconds | 1-200000         | \-           |
+------------------+-----------------------------------+------------------+--------------+
| units            |                                   | | microseconds   | microseconds |
|                  |                                   | | milliseconds   |              |
+------------------+-----------------------------------+------------------+--------------+

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
    dnRouter(cfg-action-police-tr3ccm)# excess-burst 1000 microseconds
    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# police
    dnRouter(cfg-rule-1-action-police)# meter-type tr3cm
    dnRouter(cfg-action-police-tr3cm)# excess-burst 100 milliseconds
    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# police
    dnRouter(cfg-rule-1-action-police)# meter-type sr3cm
    dnRouter(cfg-action-police-sr3cm)# excess-burst 1000 microseconds


**Removing Configuration**

To remove excess burst mode:
::

    dnRouter(cfg-action-police-tr3ccm)# no excess-burst 1000 microseconds

**Command History**

+---------+--------------------------------------------------------------+
| Release | Modification                                                 |
+=========+==============================================================+
| 13.1    | Command introduced                                           |
+---------+--------------------------------------------------------------+
| 16.1    | Split from the generic qos-policy-action-police-rate command |
+---------+--------------------------------------------------------------+
