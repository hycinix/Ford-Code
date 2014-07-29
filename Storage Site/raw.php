<html>
<head>
<title>View Raw CSV Data</title>
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
<body>

<?php
	// session_save_path("C:\RVTools\session");
	// session_start();
	
	if( !isset($_SESSION['authenticated']) || !$_SESSION['authenticated'] )
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
	
	if( isset($_SESSION['AD_Auth'] ) && $_SESSION['AD_Auth'] )
	{
		echo "<a href='index.php'>Storage</a><br/>";
		echo "<a href='health.php'>VMWare Health</a><br/>";
		echo "<a href='newFilter.php'>Create/Delete Filters</a><br/>";
		
		echo "You are logged in as: ".$_SERVER['AUTH_USER'];

		
		// echo "<form action='logout.php' method='post'>
		// <input type='submit' value='Logout' name='logout'>
		// </form>";
		
		$path = "C:\\RVTools\\CSV\\";
		
		$csvs = array();
		
		
		echo "<form action='raw.php' method='get'>
				<select name='table'>
				<option value=''>--Select Report--</option>";
		if ($handle = opendir($path)) {
			while (false !== ($csv = readdir($handle))) {
				if ('.' === $csv) continue;
				if ('..' === $csv) continue;

				$csv = explode(".",$csv);
				$csv = $csv[0];
				if( $csv != "desktop" )
				{
					array_push($csvs,$csv);
					echo "<option value='$csv'>$csv</option>";
				}
			}
			closedir($handle);
		}
		
		echo "</select>
				<input type='submit' value='Submit'>
				</form>";
		
		if( isset($_GET['table'] ) )
		{
			$name = $_GET['table'].".csv";
			$file = $path.$name;
			echo "<h3>To Download, Click <a href='CSV/$name'>$name</a></h3>";			
			$handle = fopen($file, "r");
			
			$header = fgetcsv($handle);
			
			echo "<table><tr>";
			echo "<form method='get'><input type='hidden' name='table' value='".$_GET['table']."'>";
			for( $i=0; $i < count($header); $i++ )
			{
				$head = $header[$i];
				if( stristr($head," ") )
				{
					$head = str_replace(" ","+",$head);
				}
				$current = "";
				if( isset($_GET["$head"]) )
				{
					$current = $_GET["$head"];
				}
				echo "<td>$header[$i]<br/><input type='text' name='$head' value='$current'></td>";

			}
			echo "<input type='submit' style='position: absolute; left: -9999px'/></form>";	

			echo "</tr>";
			$table = array();
			while( $row = fgetcsv($handle) )
			{
				array_push($table,$row);
			}
			for( $i=0; $i < count($table); $i++ )
			{
				$test = true;
				for( $j=0; $j < count($header); $j++ )
				{
					$head = $header[$j];
					if( stristr($head," ") )
					{
						$head = str_replace(" ","+",$head);
					}

					if( isset($_GET["$head"] ) && $_GET["$head"] )
					{
						// if( !strtolower(stristr($table[$i][$j]),strtolower($_GET["$head"])))
						if( !stristr(strtolower($table[$i][$j]),strtolower($_GET["$head"])))
						{
							$test = false;
						}
					}
				}
				if( $test )
				{
					echo "<tr>";
					
					for( $j=0; $j < count($header); $j++ )
					{
						// echo "<td>".$table[$i][$j]."</td>";
						// echo $header[$j];
						$head = str_replace(" ","%2B",$header[$j]);
						echo "<td><a href='raw.php?table=".$_GET['table']."&".$head."=".$table[$i][$j]."'>".$table[$i][$j]."</a></td>";
					}
					
					echo "</tr>";
				}
			}
			echo "</table>";
		}
	}
	else
	{
		echo "nope";
	}
?>

</body>
</html>