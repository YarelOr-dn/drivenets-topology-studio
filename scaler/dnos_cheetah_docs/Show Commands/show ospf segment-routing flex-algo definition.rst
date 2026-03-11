show ospf segment-routing flex-algo definition
----------------------------------------------

**Minimum user role:** viewer

To display the Flex-Algo definition (per received FAD).

**Command syntax: show ospf** instance [ospf-instance-name] **segment-routing flex-algo definition** [flex-algo-id]

**Command mode:** operational

.. **Note**

	- use "instance [ospf-instance-name]" to display information from a specific OSPF instance; when not specified, display information from all ospf instances

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                              |
+====================+==========================================================================================================================+
| ospf-instance-name | Filters the displayed information to the specified instance                                                              |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| flex-algo          | Displays definition of the requested <flex-algo id>. If not defined, will display all definitions                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+

**Example**
::

  dnRouter# show ospf segment-routing flex-algo definition 130
  Ospf Instance OSPF-1
  Area 0.0.0.0:
  Flex Algorithm 130
    Color: 5
    Description: this is a description for algo 130.
    Definition
      None

  Area 20.20.20.20:
  Flex Algorithm 131
    Color: 7
    Description: this is a description for algo 131.
    Definition
      Advertised system: 11.11.11.11, Priority: 10
      Metric: te-metric, Calculation: spf
      Flags: 0x80000000
      FAPM supported: Yes
      FAD is supported
    Participates
      8 nodes
      26 links

  Area 40.40.40.40:
  Flex Algorithm 132
    Color: 8
    Description: this is a description for algo 132.
    Definition
      Advertised system: 33.33.33.33, Priority: 255
      Metric: link-delay, Calculation: spf
      Flags: 0x80000111
      FAPM supported: Yes
      Participation withdrawn due to unsupported FAD flags
    Participates
      0 nodes
      0 links


.. **Help line:**

**Command History**

+---------+-----------------------------------------------------------+
| Release | Modification                                              |
+=========+===========================================================+
| 19.1    | Command introduced                                        |
+---------+-----------------------------------------------------------+