protocols segment-routing mpls policy binding-sid
-------------------------------------------------

**Minimum user role:** operator

Set a statically configured binding-SID to be assigned for a given SR-TE policy.
When configured with a value, the binding-SID label value must match an available label within the configured SRLB.
When set to dynamic (default behavior), the system automatically allocates a binding-SID label for the SR-TE policy from the dynamic label range.
When the policy is in the Up state, and the mpls ILM entry is installed in the FIB with an ingress label matching the requested binding-SID label, and the egress operation of the pop and push policy label stack.
To configure the policy binding-SID:

**Command syntax: binding-sid [binding-sid]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Note**
- The system default behavior is to select a policy binding-SID from the dynamic label range.
- The user may configure the binding-SID value, required to do a commit validation that the configured value matches the configured SRLB.
- The commit validation that the configured binding-SID label value does not conflict with any other configured binding-SID or adjacency-SID.
- The configured binding-SID by value is persistent for the given policy throughout the policy lifetime,and expected to be preserved after the system reboot.
- Reconfiguration of the binding-SID, regardless of changing the value or adding/removing a config does not change the policy state.

**Parameter table**

+-------------+--------------------------------------------+-------+---------+
| Parameter   | Description                                | Range | Default |
+=============+============================================+=======+=========+
| binding-sid | Configure binding-sid value for the policy | \-    | dynamic |
+-------------+--------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# binding-sid 8003


**Removing Configuration**

To return to default binding-sid allocation:
::

    dnRouter(cfg-igp-mpls-policy)# no binding-sid

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
