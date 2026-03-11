qos policy rule action police meter-type sr2cm rank
---------------------------------------------------

**Minimum user role:** operator



Policer rank in hierarchy. Policer with higher rank share unused tokens with lower rank policers. Rank 1 is not configured directly, rather derived from parent policer. 

 A hierarchical policer can be configured to enforce strict policing, according to its CIR (and EIR) settings, and never use tokens from higher rank policers. The hierarchical policer does pass unused tokens to lower rank policers regardless of the strict setting.

**Command syntax: rank [rank]** strict

**Command mode:** config

**Hierarchies**

- qos policy rule action police meter-type sr2cm

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| rank      | Policer rank in hierarchy. Policer with higher rank share unused tokens with     | 2-4   | \-      |
|           | lower rank policers. Rank 1 is not configured directly, rather derived from      |       |         |
|           | parent policer.                                                                  |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+
| strict    | A strict hierarchical policer does not use tokens from higher rank meters, hence | \-    | \-      |
|           | enforce the CIR (and EIR) rates strictly. The hierarchical policer does pass     |       |         |
|           | unused tokens to lower rank policers regardless of the strict setting.           |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# police
    dnRouter(cfg-rule-1-action-police)# meter-type tr3cm
    dnRouter(cfg-action-police-tr3cm)# rank 2
    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# police
    dnRouter(cfg-rule-1-action-police)# meter-type tr3cm
    dnRouter(cfg-action-police-tr3cm)# rank 2 strict


**Removing Configuration**

To remove the policer rank:
::

    dnRouter(cfg-action-police-tr3ccm)# no rank

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
