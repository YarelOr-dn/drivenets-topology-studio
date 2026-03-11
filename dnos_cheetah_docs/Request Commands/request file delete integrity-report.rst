request file delete integrity-report
-------------------------------------

**Minimum user role:** admin

**Command syntax: request file delete integrity-report**  **[file-name]**

**Description:** Delete the named integrity-report file.

**Example:**
::

	dnRouter# request file delete integrity-report integrity_report_dnRouter_20231019_045439.json.gz

	Warning: Are you sure you want to delete integrity_report_dnRouter_20231019_045439.json.gz? (yes/no) [no]? yes
	File integrity_report_dnRouter_20231019_045439.json.gz has been deleted successfully

**Command mode:** operational

**Note:**

- Validation : User Yes/no question with the specified file name.

**Help line:** Files from the integrity-report directory

**Parameter table:**

+-----------+------------------------------------------+---------------+
| Parameter | Values                                   | Default value |
+===========+==========================================+===============+
| file-name | Name of integrity-report file to delete. |               |
+-----------+------------------------------------------+---------------+

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.3    | Command introduced                  |
+---------+-------------------------------------+
