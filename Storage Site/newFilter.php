<html>
<head>
<title>Modify Custom Filters</title>
<style>
body
{
	font-style: normal;
	font-family: "Courier New", Courier, monospace;
}
</style>
</head>
<body>

<?php

// session_save_path("C:\RVTools\session");
// session_start();
if( !isset($_SESSION['authenticated']) || !$_SESSION['authenticated'])
{
	header( "location: logout.php" );
}
else if( !isset($_SESSION['AD_Auth']) || !$_SESSION['AD_Auth'])
{
	header( "location: index.php" );
}

// Timeout after 10 minutes
if( isset($_SESSION['timeout']) )
{
	if( $_SESSION['timeout'] + (10*60) < time() )
	{
		session_destroy();
		header("location: logout.php");
	}
}
$_SESSION['timeout'] = time();

if( isset($_SESSION['AD_Auth']) && $_SESSION['AD_Auth'] )
{
	echo "<a href='index.php'>Storage</a><br/>";
	echo "<a href='health.php'>VMWare Health</a><br/>";
	echo "<a href='raw.php'>Access Raw RVTools Data</a><br/>";
	
	echo "You are logged in as: ".$_SERVER['AUTH_USER'];

	
	// echo "<form action='logout.php' method='post'>
	// <input type='submit' value='Logout' name='logout'>
	// </form>";
	
	
	echo "<form action='newFilter.php' method='post'>
Name: <input type='text' name='name'><br/>
Servers(separate with commas, do not use spaces) <input type='text' name='servers'><br/>
<input type='submit' value='Submit'>
</form>";

	$path = "C:\\RVTools\\filter\\";

	if( isset( $_POST['name'] ) && isset( $_POST['servers'] ) )
	{
		$name = $_POST['name'];
		$servers = explode(",",$_POST['servers'] );
		$file = fopen($path."$name".".txt","w");
		
		for( $i=0; $i < count($servers); $i++ )
		{
			fwrite( $file, strtoupper($servers[$i])."\r\n");
		}
		fclose($file);
	}

	if( isset($_POST['delete'] ) )
	{
		$filter = $_POST['delete'];
		unlink( $path.$filter.".txt");
	}

	echo "Select Filter to Delete<br/>
	<form action='newFilter.php' method='post'>
	<select name='delete'>
	<option value=''>--Select a Filter--</option>";
	if ($handle = opendir($path)) {
		while (false !== ($filters = readdir($handle))) {
			if ('.' === $filters) continue;
			if ('..' === $filters) continue;

			$filters = explode(".",$filters);
			$name = $filters[0];
			echo "<option value='$name'>Servers Owned by $name</option>";
		}
		closedir($handle);
		echo "<br/>";
	}
	echo "<input type='submit' value='Delete'></select></form";
}
?>

</body>
</html>