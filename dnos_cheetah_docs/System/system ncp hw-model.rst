system ncp hw-model
-------------------

**Minimum user role:** operator

To configure the model of the NCP:

**Command syntax: ncp [ncp-id] hw-model [hw-model]**

**Command mode:** config

**Hierarchies**

- system ncp


**Note**

- "hw-model" is a optional parameter for NCPs. If not set, a hardware model is automatically configured. The default values is determined by the ncp model.

- If the hw-model is not the default selected per the ncp model, it must be configured for correct operation.

- For **standalone cluster**, NCP 0 is configured by system. You cannot remove ncp-0 configuration.

- Validate that Hardware model not compatible with the ncp model cannot be set

**Parameter table**

+-----------+--------------------------+------------------------------------+--------------------+
| Parameter | Description              | Allowed hw-models per ncp model    | Default            |
+===========+==========================+====================================+====================+
| hw-model  | The NCP hardware model   | NCP-40C: S9700-53DX, AGCXD40S      | S9700-53DX         |
|           |                          | NCP-10CD: S9700-23D                | S9700-23D          |
|           |                          | NCP-36CD-S: S9710-76D              | S9710-76D          |
|           |                          | NCP-36CD-S-SA: S9610-36D           | S9610-36D          |
+-----------+--------------------------+------------------------------------+--------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# hw-model S9700-53DX


**Removing Configuration**

To revert the NCP configuration to default:
::

    dnRouter(cfg-system)# no ncp 7

.. **Help line:** configure NCP hardware model

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 16.2    | Command introduced                 |
+---------+------------------------------------+
