system utilization node-type cpu cpu-util-threshold
---------------------------------------------------

**Minimum user role:** operator

"To configure the CPU utilization rate threshold:"


**Command syntax: cpu-util-threshold [cpu-util-threshold]**

**Command mode:** config

**Hierarchies**

- system utilization node-type cpu

**Note**
- "The command is applicable to the platform CPU utilization threshold."


**Parameter table**

+--------------------+-------------+-------+---------+
| Parameter          | Description | Range | Default |
+====================+=============+=======+=========+
| cpu-util-threshold | percentage  | 0-100 | 90      |
+--------------------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# utilization
    dnRouter(cfg-system-util)# node-type ncp
    dnRouter(cfg-system-util-ncp)# cpu
    dnRouter(cfg-system-util-ncp-cpu)# cpu-util-threshold 90


**Removing Configuration**

To set cpu utilization rate threshold to default:
::

    dnRouter(cfg-system-util-ncp-cpu)# no cpu-util-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
