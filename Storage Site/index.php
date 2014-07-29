<html>
<head>
<title>Storage Report</title>
<style>
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

// Timeout after 10 minutes
if( isset($_SESSION['timeout']) )
{
	if( $_SESSION['timeout'] + (10*60) < time() )
	{
		header("location: logout.php");
	}
}
$_SESSION['timeout'] = time();




// Test for AD membership to authenticate
$conn=ldap_connect("ldap://ffnyc-60-012.fordfound.org");

ldap_set_option($conn, LDAP_OPT_REFERRALS, 0);
ldap_set_option($conn, LDAP_OPT_PROTOCOL_VERSION, 3);
if( $conn )
{
	$_SESSION['AD_Auth'] = false;
	// if( ldap_bind($conn, "b.marks@fordfound.org", "VfR4%tGb" ))
	if( ldap_bind($conn, "s.storage@fordfound.org", '8p9JhvZSX33Uw&Tr,PYc' ))
	// if( ldap_bind($conn ) )
	{
		$user = explode("\\",$_SERVER['AUTH_USER']);
		if( $user[0] == 'FORDFOUNDATION' )
		{
				
			$user = $user[1];
			$group = "StorageReportUsers";
			$result=ldap_search($conn, "DC=fordfound,DC=org", "(&(objectCategory=person)(sAMAccountName=$user))");
			$data = ldap_get_entries( $conn, $result );
			foreach( $data[0]['memberof'] as $grp )
			{
				$grp = explode(",",$grp);
				$grp = explode("CN=",$grp[0]);
				if( isset($grp[1] ) )
				{
					if( $grp[1] == $group )
					{
						$_SESSION['AD_Auth'] = true;
					}
				}
			}
		}
	}
	// else
	// {
		// ldap_get_option( $conn, 0x0032, $err );
		// echo "<br/>".$err."<br/>";
	// }
}
ldap_close($conn);

if( isset( $_SESSION['AD_Auth'] ) && $_SESSION['AD_Auth'] )
{
	$_SESSION['authenticated'] = true;
}
else
{
	if ( isset($_POST["password"]) && $_POST['password'] == 'carrots' )
	{
		$_SESSION['authenticated'] = true;
	}

	else if( ( isset($_POST["password"]) && $_POST['password'] == 'rvtools' ) )
	{
		$_SESSION['authenticated'] = true;
		$_SESSION['raw'] = true;
		header("location: raw.php");
	}
	else
	{
		$_SESSION['authenticated'] = false;
	}
}

// if( isset($_POST["logout"] ) && $_POST['logout'])
// {
	// $_SESSION['authenticated'] = false;
// }


$defaultFilter = "IT";

if( $_SESSION['authenticated'] )
{
	if( !isset($_GET['filter']) || !$_GET['filter'] )
	{
		header( "location: ?filter=$defaultFilter");
	}
	
	
	$filename = "C:\RVTools\CSV\RVTools_tabvPartition.csv";
		
	$file = fopen("$filename","r");

	$header = fgetcsv($file);

	$order = array();
	// $order = ["VM","Disk","Capacity MB","Free MB","Free %","Purpose","Tier","Owner","OS"];
	$order[0] = "VM";
	$order[1] = "Disk";
	$order[2] = "Capacity MB";
	$order[3] = "Free MB";
	$order[4] = "Free %";
	$order[5] = "Purpose";
	$order[6] = "Tier";
	$order[7] = "Owner";
	$order[8] = "OS";	
	
	$hash = array();

	$hash["VM"] = 0;
	$hash["Disk"] = 1;
	$hash["Capacity MB"] = 2;
	$hash["Free MB"] = 3;
	$hash["Free %"] = 4;
	$hash["Purpose"] = 6;
	$hash["Tier"] = 7;
	$hash["Owner"] = 8;
	$hash["OS"] = 12;
	
	echo "<a href='health.php'>VMWare Health</a><br/>";
	
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
	
	$filter = $_GET['filter'];
			
	echo "<form action='index.php?filter=$filter' method='post'>
			<input type='submit' value='Clear Filters' name='Clear'>
			</form>";

	date_default_timezone_set('America/New_York');
	echo "<p align='right'>This report was taken on: ".date("F d Y H:i:s",filemtime($filename))."</p>";
	
	echo "<form action='index.php' method='get'>
			<select name='filter'>
			<option value=''>-Report Filter-</option>
			<option value='IT'>Display All</option>
			<option value='bsd'>BSD Report</option>
			<option value='lowmedium'>Low to Medium Risk</option>
			<option value='high'>High Risk</option>";
	
	
	$path = "C:\\RVTools\\filter\\";
	
	$names = array();

	if ($handle = opendir($path)) {
		while (false !== ($filters = readdir($handle))) {
			if ('.' === $filters) continue;
			if ('..' === $filters) continue;

			$filters = explode(".",$filters);
			$name = $filters[0];
			array_push($names,$name);
			echo "<option value='$name'>Servers Owned by $name</option>";
		}
		closedir($handle);
	}
	
	
	echo "</select>
			<input type='submit'>
			</form>";

	$table = array();
	while( $row = fgetcsv($file))
	{
		array_push($table,$row);
	}

	function cmpName( $a, $b )
	{
		return strtolower($a[0]) - strtolower($b[0]);
	}
	usort($table,"cmpName");

	function cmp( $a, $b )
	{
		return $a[4] - $b[4];
	}
	usort($table,"cmp");

		
	echo "<table><tr>";
	echo "<form method='get'><input type='hidden' name='filter' value='".$_GET['filter']."'>";
	for( $i=0; $i < count($order); $i++ )
	{
		$head = $header[$hash[$order[$i]]];
		echo "<td><b>".$head."</b><br/>";
		if( $head != "Capacity MB" && !stristr($head,"Free") )//Free MB and Free %
		{
			$current = "";
			if( isset($_GET["$head"]) )
			{
				$current = $_GET["$head"];
			}
			echo "<input type='text' name='$head' value='$current'>";
		}
		echo "</td>";
	}
	echo "<td><b>Target Percent to Free</b></td>";
	echo "<td><b>Target Space to Delete (Mbs)</b></td>";
	echo "<input type='submit' style='position: absolute; left: -9999px'/>";
	echo "</form>";	
	echo "</tr>";

	$filter = $_GET["filter"];
	if( in_array( $filter, $names ) )
	{
		$servers = file( $path.$filter.".txt" );
		for( $i=0; $i < count($servers); $i++ )
		{
			$servers[$i] = trim($servers[$i]);
		}
	}
	for( $row = 0; $row < count($table); $row++ )
	{
		$test = $table[$row][$hash["Owner"]] == "BSD";
		if( isset($_GET["filter"] ))
		{
			if( $filter == "bsd" )
			{
				$test = $table[$row][$hash["Owner"]] == "BSD";
			}
			else if( $filter == "lowmedium" )
			{
				$test = $table[$row][$hash["Owner"]] == "BSD" && $table[$row][$hash["Free %"]] < 10;
			}
			else if( $filter == "high" )
			{
				$test = $table[$row][$hash["Owner"]] == "BSD" && $table[$row][$hash["Free %"]] < 10 && $table[$row][$hash["Disk"]] == "C:\\" && $table[$row][$hash["Tier"]] == "Prod";
			}
			else if( $filter == "IT" )
			{
				$test = true;
			}
			else if( in_array($filter,$names) )
			{
				$test = in_array( strtoupper($table[$row][$hash["VM"]]), $servers );
			}
			else
			{
				$test = false;
			}
		}
		
		for( $i=0; $i < count($order); $i++ )
		{
			$head = $header[$hash[$order[$i]]];
			if( isset($_GET["$head"] ) && $_GET["$head"] )
			{
				if( !stristr($table[$row][$hash["$head"]],$_GET["$head"]))
				{
					$test = false;
				}
			}
		}
		if( $test )
		{
		
			$targetPercent = 0;
			if( 10 - $table[$row][$hash["Free %"]] > 0 )
			{
				$targetPercent = 10 - $table[$row][$hash["Free %"]];
			}

			if( $targetPercent > 0 )
			{
				echo "<tr style='color:red; font-weight:bold;'>";
			}
			else
			{
				echo "<tr>";
			}
			
			
			// echo "<tr>";
			for( $i=0; $i < count($order); $i++ )
			{
				if( $order[$i] != "Capacity MB" && !stristr($order[$i],"Free") )//Free MB and Free %
				{
					echo "<td><a href='index.php?filter=$defaultFilter&".$order[$i]."=".$table[$row][$hash[$order[$i]]]."'>".strtoupper($table[$row][$hash[$order[$i]]])."</a></td>";
				}
				else
				{
					echo "<td>".$table[$row][$hash[$order[$i]]]."</td>";
				}
			}
			
			$capacity = floatval(str_replace(',','',$table[$row][$hash["Capacity MB"]]));
			$targetSpace = ($capacity * $targetPercent / 100 );
			
			
			echo "<td>$targetPercent</td>";
			echo "<td>$targetSpace</td>";
			
			

			
			if( $targetPercent > 0 )
			{
				echo "</tr>";
			}
			else
			{
				echo "</tr>";
			}

			// echo "</tr>";
		}
		
		// echo "<tr>";
			// for( $i=0; $i < count($order); $i++ )
			// {
				// echo "<td>".$table[$row][$hash[$order[$i]]]."</td>";
			// }
			// $targetPercent = 0;
			// if( 10 - $table[$row][$hash["Free %"]] > 0 )
			// {
				// $targetPercent = 10 - $table[$row][$hash["Free %"]];
			// }

			// if( $targetPercent > 0 )
			// {
				// echo "<td style='color:red'><b>";
			// }
			// else
			// {
				// echo "<td>";
			// }
			
			// echo $targetPercent;

			// if( $targetPercent > 0 )
			// {
				// echo "</td></b>";
			// }
			// else
			// {
				// echo "</td>";
			// }
			
			
			// $capacity = floatval(str_replace(',','',$table[$row][$hash["Capacity MB"]]));
			// $targetSpace = ($capacity * $targetPercent / 100 );
			
			
			// if( $targetPercent > 0 )
			// {
				// echo "<td style='color:red'><b>";
			// }
			// else
			// {
				// echo "<td>";
			// }
			
			// echo $targetSpace;
			
			// if( $targetPercent > 0 )
			// {
				// echo "</td></b>";
			// }
			// else
			// {
				// echo "</td>";
			// }

			// echo "</tr>";
		// }
	}

	echo "</table>";
	fclose($file);
}
else
{
	echo "<form action='$url'  method='post'>
		Password: <input type='password' name='password'>
		<input type='submit' value='Submit'>
		</form>";
		
	echo "You do not have permission to view this page<br/>Please login to continue";
}

// Pear Mail Library
// require_once "Mail.php";

// $from = '<b.marks@fordfound.org>';
// $to = '<b.marks@fordfound.org>';
// $subject = 'Hi!';
// $body = "Hi,\n\nHow are you?";

// $headers = array(
    // 'From' => $from,
    // 'To' => $to,
    // 'Subject' => $subject
// );

// $smtp = Mail::factory('smtp', array(
        // 'host' => 'smtp.fordfound.org',
        // 'port' => '25',
        // 'auth' => true,
        // 'username' => 'b.marks@fordfound.org',
        // 'password' => 'CdE3$rFv'
    // ));

// Commented out to avoid spam
// $mail = $smtp->send($to, $headers, $body);

// if (PEAR::isError($mail)) {
    // echo('<p>' . $mail->getMessage() . '</p>');
// } else {
    // echo('<p>Message successfully sent!</p>');
// }

?>

</body>
</html>