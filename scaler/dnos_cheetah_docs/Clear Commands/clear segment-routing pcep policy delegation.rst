clear segment-routing pcep policy delegation
--------------------------------------------

**Minimum user role:** operator

To flush the PCE ERO for a PCC delegated policy path:

**Command syntax: clear segment-routing pcep policy delegation** {policy [policy-name] | policy [policy-name] path [path-name]

**Command mode:** operation

.. **Hierarchies**

**Note**

 - Apply only for PCC initiated 'pcep-delegation' paths.
 - The policy path remains delegated to the active PCE.
 - The policy path will clear its ERO and change to a down state.


**Parameter table:**

+-----------------+----------------------------------------------------+-----------+-------------+
| Parameter       | Description                                        | Range     | Default     |
+=================+====================================================+===========+=============+
| policy-name     | Clear all delegated path of specific policy        | string    | \-          |
+-----------------+----------------------------------------------------+-----------+-------------+
| path-name       | Clear specific delegated path of specific policy   | string    | \-          |
+-----------------+----------------------------------------------------+-----------+-------------+


**Example**
::

	dnRouter# clear segment-routing pcep policy delegation
	dnRouter# clear segment-routing pcep policy delegation policy SR_TE_POLICY_1
    dnRouter# clear segment-routing pcep policy delegation policy SR_TE_POLICY_1 path PCEP_PATH_2



**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 19.1        | Command introduced    |
+-------------+-----------------------+