request security generate certificate-signing-request - supported in 19.1version
--------------------------------------------------------------------------------

**Command syntax: request security generate certificate-signing-request [request-id] key-pair [key-id] dn [dn]**

**Description:** generates CRS (Certificate Signing Request) for CA (Certification Authority).

**CLI example:**
::

	dnRouter# request security generate certificate-signing-request myCRS key-pair myCertificateKeys subject CN=John Smith,OU=Support,O=DRIVENETS,ST=CA,C=US,L=San Francisco,MAIL=john.smith@drivenets.com
	
	Generate Certificate Signing Request:
	
	-----BEGIN CERTIFICATE REQUEST-----
	MIICzDCCAbQCAQAwgYYxCzAJBgNVBAYTAkVOMQ0wCwYDVQQIDARub25lMQ0wCwYD
	VQQHDARub25lMRIwEAYDVQQKDAlXaWtpcGVkaWExDTALBgNVBAsMBG5vbmUxGDAW
	BgNVBAMMDyoud2lraXBlZGlhLm9yZzEcMBoGCSqGSIb3DQEJARYNbm9uZUBub25l
	LmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAMP/U8RlcCD6E8AL
	PT8LLUR9ygyygPCaSmIEC8zXGJung3ykElXFRz/Jc/bu0hxCxi2YDz5IjxBBOpB/
	kieG83HsSmZZtR+drZIQ6vOsr/ucvpnB9z4XzKuabNGZ5ZiTSQ9L7Mx8FzvUTq5y
	/ArIuM+FBeuno/IV8zvwAe/VRa8i0QjFXT9vBBp35aeatdnJ2ds50yKCsHHcjvtr
	9/8zPVqqmhl2XFS3Qdqlsprzbgksom67OobJGjaV+fNHNQ0o/rzP//Pl3i7vvaEG
	7Ff8tQhEwR9nJUR1T6Z7ln7S6cOr23YozgWVkEJ/dSr6LAopb+cZ88FzW5NszU6i
	57HhA7ECAwEAAaAAMA0GCSqGSIb3DQEBBAUAA4IBAQBn8OCVOIx+n0AS6WbEmYDR
	SspR9xOCoOwYfamB+2Bpmt82R01zJ/kaqzUtZUjaGvQvAaz5lUwoMdaO0X7I5Xfl
	sllMFDaYoGD4Rru4s8gz2qG/QHWA8uPXzJVAj6X0olbIdLTEqTKsnBj4Zr1AJCNy
	/YcG4ouLJr140o26MhwBpoCRpPjAgdYMH60BYfnc4/DILxMVqR9xqK1s98d6Ob/+
	3wHFK+S7BRWrJQXcM8veAexXuk9lHQ+FgGfD0eSYGz0kyP26Qa2pLTwumjt+nBPl
	rfJxaLHwTQ/1988G0H35ED0f9Md5fzoKi5evU1wG5WRxdEUPyt3QUXxdQ69i0C+7
	-----END CERTIFICATE REQUEST-----
	
	
	
**Command mode:** operational

**TACACS role:** operator

**Note:**

-  DN (Distinguished Names) may include the following:

   -  CN - Common Name

   -  OU - Orgranizational Unit name

   -  O - Organization name

   -  S - State (2 letters code)

   -  C - Country

   -  L - City

   -  MAIL - e-mail address

-  DN (Distingushed Names) are separated by comma (,)

-  CRS files are stored in the folder /security/crs/

**Help line:**

**Parameter table:**

+------------+-----------------------+---------------+
| Parameter  | Values                | Default value |
+============+=======================+===============+
| request-id | string                |               |
+------------+-----------------------+---------------+
| key-id     | Any existing key-pair |               |
+------------+-----------------------+---------------+
| dn         | string                |               |
+------------+-----------------------+---------------+
