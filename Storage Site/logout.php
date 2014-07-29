<html>
<head>
<title>Logout</title>
</head>
<body>

<?php

	// session_start();
	session_destroy();
	header( "location: index.php" );

?>


</body>
</html>