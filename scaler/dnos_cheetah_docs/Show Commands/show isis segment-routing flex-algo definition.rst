show isis segment-routing flex-algo definition
----------------------------------------------

**Minimum user role:** viewer

To display the Flex-Algo definition (per received FAD).

**Command syntax: show isis** instance [isis-instance-name] **segment-routing flex-algo definition** [flex-algo-id]

**Command mode:** operational

.. **Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when not specified, display information from all isis instances

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                              |
+====================+==========================================================================================================================+
| isis-instance-name | Filters the displayed information to the specified instance                                                              |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| flex-algo          | Displays definition of the requested <flex-algo id>. If not defined, will display all definitions                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+

**Example**
::

  e2e_R1_1# show isis segment-routing flex-algo definition 130
  Instance one
  Level 1:
  Flex Algorithm 130
    Color: 30
    Description: this is a description for algo 130. it is a wonderful algo.
    Definition
      None

  Level 2:
  Flex Algorithm 130
    Color: 30
    Description: this is a description for algo 130. it is a wonderful algo.
    Definition
      Advertised system: e2e_R8_1, Priority: 10
      Metric: te-metric, Calculation: spf
    Participates
      8 nodes
      26 links


.. **Help line:**

**Command History**

+---------+-----------------------------------------------------------+
| Release | Modification                                              |
+=========+===========================================================+
| 18.0    | Command introduced                                        |
+---------+-----------------------------------------------------------+