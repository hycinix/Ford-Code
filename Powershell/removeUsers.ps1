Import-Module ActiveDirectory;
$log = "C:\log.txt";
$users = Get-Content "C:\users.txt";
for( $i=0; $i -lt $users.count; $i++ )
{
	$msg = "Removing " $users[$i]
	echo $msg
	Try
	{
		Remove-ADUser -Identity $users[$i];
		$err = "Removed user " + $users[$i];
		$err >> $log
	}
	Catch
	{
		$err = "ERROR,Removing user " + $users[$i];
		$err >> $log
		$error[0] >> $log
	}
}