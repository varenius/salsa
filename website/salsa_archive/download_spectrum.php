<?php 
// This file gets data from the SALSA archive when sent a specific ID. This file
// is not intented to be used directly, rather links to this file with specific
// ids are provided by another piece of code, e.g. shown in an table.
$id = htmlspecialchars($_GET["id"]);
$kind = htmlspecialchars($_GET["kind"]);
// Connect to database. This should be made safe
mysql_connect("localhost","salsa_archiver","PASSWORD"); 
mysql_select_db("salsa_vale_drupa"); 
// Get data
$query = "SELECT " . $kind . " FROM salsa_archive where id=$id"; 
$result = mysql_query($query) or die (mysql_error()); 
$arr = mysql_fetch_array($result); 
$data = $arr[0];
// Send data to browser
if ($kind=='file_fits')
    {
    header("Content-Disposition: attachment; filename=\"spectrum_" . $id. ".fits\"");
    header("Content-type: application/octet-stream");
}
elseif ($kind=='file_png')
{
    header("Content-Disposition: attachment; filename=\"spectrum_" . $id. ".png\"");
    header("Content-type: image/png");
}
print $data; 
?> 