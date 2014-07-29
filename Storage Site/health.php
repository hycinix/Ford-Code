<html>
<head>
<title>VM Health</title>
<style>
table
{
	width: 100%;
}
table,tr,td
{
	border-collapse: collapse;
	border:1px solid black;
	text-align: right;
}
body
{
	font-style: normal;
	font-family: "Courier New", Courier, monospace;
}

tr:nth-child(even) {
    background-color: #8FD8D8;
}

tr:nth-child(odd) {
    background-color: #A2A9AF;
}
</style>
</head>
<body>

<?php

$url = $_SERVER['REQUEST_URI'];

// session_save_path("C:\RVTools\session");
// session_start();

if( !isset($_SESSION['authenticated']) || !$_SESSION['authenticated'] )
{
	header( "location: logout.php" );
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

if( isset($_SESSION['authenticated']) && $_SESSION['authenticated'] )
{
	$filename = "C:\RVTools\CSV\RVTools_tabvHealth.csv";
		
	$file = fopen("$filename","r");

	$header = fgetcsv($file);
	
	echo "<a href='index.php'>Storage</a><br/>";
	
	if( isset($_SESSION['AD_Auth']) && $_SESSION['AD_Auth'] )
	{
		echo "<a href='raw.php'>Access Raw RVTools Data</a><br/>";
		echo "<a href='newFilter.php'>Create/Delete Filters</a><br/>";
		
		echo "You are logged in as: ".$_SERVER['AUTH_USER'];
	}
	else
	{
		echo "<form action='index.php' method='post'>
				<input type='submit' value='Logout' name='logout'>
				</form>";
	}
	
	echo "<form action='health.php' method='post'>
			<input type='submit' value='Clear Filter' name='Clear'>
			</form>";

	date_default_timezone_set('America/New_York');
	echo "<p align='right'>This report was taken on: ".date("F d Y H:i:s",filemtime($filename))."</p>";
	

	$table = array();
	
	while( $row = fgetcsv($file))
	{
		array_push($table,$row);
	}
	
	$messages = array();
	array_push($messages,"--Select an Error--</option>");

	array_push($messages,"Disk Space Available");
	for( $i=0; $i < count($table); $i++ )
	{
		$error = $table[$i][1];
		$error = explode("!",$error);
		if( !stristr($error[0],"disk space") )
		{
			array_push($messages,$error[0]);
		}
	}
	
	$messages = array_unique($messages);
	sort($messages);
	
	function cmp( $a, $b )
	{
		return (strtolower($a[0]) < strtolower($b[0])) ? -1 : 1;
	}
	usort($table,"cmp");

	echo "<form action='health.php' method='get' align='right'>
			<select name='err'>";
	for( $i=0; $i < count($messages); $i++ )
	{
		$message = $messages[$i];
		echo "<option value='$i'>$message</option>";
	}
	echo "</select>
			<input type='submit' value='Submit'>
			</form>";
	
	echo "<table>
			<tr style='font-weight: bold'>";
	
	for( $i=0; $i < count($header); $i++ )
	{
		echo "<td>".$header[$i]."</td>";
	}
	
	for( $i=0; $i < count($table); $i++ )
	{
		if( !isset($_GET['err']) || !($_GET['err']) || stristr($table[$i][1],$messages[$_GET['err']]) )
		{
			echo "<tr>";
			
			for( $j=0; $j < count($table[$i]); $j++ )
			{
				echo "<td>".$table[$i][$j]."</td>";
			}
			
			echo "</tr>";
		}
	}
	
	echo "</tr>
			</table>";
	
	fclose($file);
}
else
{
	header("Location: index.php");
}
?>

</body>
</html>
