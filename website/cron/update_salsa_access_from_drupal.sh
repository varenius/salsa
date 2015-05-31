#!/bin/bash

# The path to a directory which contents should be copied to user home directory during user creation
skel_dir="/opt/salsa/skel"

# The MySQL user and password with which to login on the webserver.
# For security reasons this user should only be able to do SELECT on the database specified below
mysql_user="salsa_drupal"
mysql_password="PASSWORD"

# The hostname of the webserver.
# On a one computer configuration where the webserver is the same as the telescope computer this should be set to "localhost"
mysql_host="localhost"

# The name of the MySQL database on the webserver
mysql_db_name="salsa_drupal"

logfile="/opt/salsa/crontab/update_salsa_users.log"

# This is the default shell that users get when they login to the telescope computer
default_shell="/bin/bash"

telescope_name='Vale' # As in drupal NODE table

telescope_id=$(/usr/bin/mysql -u "$mysql_user" --host="$mysql_host" --password="$mysql_password" --silent --skip-column-names "$mysql_db_name" -e "SELECT node.nid FROM node WHERE node.title='$telescope_name' AND node.type = 'telescope';")
# Need to select on type telescope. If not, select will match also merci_reservations with title = telescope_name,
# i.e. problems if a reservation is called "Vale" since multiple rows will be returned.
echo "ID for this telescope:"
echo $telescope_id

booked_user=$(/usr/bin/mysql -u "$mysql_user" --host="$mysql_host" --password="$mysql_password" --silent --skip-column-names "$mysql_db_name" -e "SELECT users.name FROM users INNER JOIN node ON users.uid=node.uid INNER JOIN field_data_field_merci_date ON node.nid=field_data_field_merci_date.entity_id INNER JOIN merci_reservation_detail ON merci_reservation_detail.nid=field_data_field_merci_date.entity_id WHERE merci_reservation_detail.merci_item_nid=$telescope_id AND field_merci_date_value < UTC_TIMESTAMP() AND field_merci_date_value2 > UTC_TIMESTAMP();")
echo "Currently booked user:"
echo $booked_user 

if [ -n "$booked_user" ]; then
    # Only update user if there is a booking. If no booking, booked user will be empty.
    booked_user_passwd=$(/usr/bin/mysql -u "$mysql_user" --host="$mysql_host" --password="$mysql_password" --silent --skip-column-names "$mysql_db_name" -e "SELECT field_observation_password_value FROM field_data_field_observation_password INNER JOIN users ON field_data_field_observation_password.entity_id=users.uid WHERE users.name='$booked_user';")

    # only change things for users, not for admin
    if [ "$booked_user" != "salsa_admin" ]; then
    # If the user doesn't exist
        if !( id $booked_user > /dev/null 2>&1 ) ; then
            echo "$(date): Adding user $booked_user" >> $logfile
            # Create the user
            /usr/sbin/useradd --create-home --skel "$skel_dir" -s /usr/sbin/nologin $booked_user >> $logfile 2>&1
            # Add user to group salsa_users, used to make sure we only kick out users, not admin
            /usr/bin/gpasswd -a $booked_user salsa_users >> $logfile 2>&1
            # User was created, change password for user to chosen in Drupal
            echo "$(date): Changing password for new user $booked_user" >> $logfile
            echo $booked_user:$booked_user_passwd | /usr/sbin/chpasswd  >> $logfile 2>&1

        else
            # User already exists, change password for user to chosen in Drupal
            #echo "$(date)" >> $logfile
            #echo "Changing password for old user $booked_user" >> $logfile
            #echo $booked_user:$booked_user_passwd | /usr/sbin/chpasswd  >> $logfile 2>&1
            echo $booked_user:$booked_user_passwd | /usr/sbin/chpasswd  >> /dev/null 2>&1
        fi;
    fi;
fi;

# Loop through all unix users in the group salsa_users, will kick out user if not booked.
for user in $( members salsa_users ); do
    if [ "$user" == "$booked_user" ]; then
        # Enable the currently booked user by assigning real login shell (i.e. bash)
        /usr/sbin/usermod -s $default_shell $user >> /dev/null 2>&1
    else
        # If the user is still logged in after his/her booking, kill all processes running and force logout the user.
        /usr/bin/pkill -KILL -u $user >> /dev/null 2>&1
        # Remove lock file created by singelton instance
        if [ -a "/tmp/-opt-salsa-controller-SALSA-.lock" ]; then 
            rm /tmp/-opt-salsa-controller-SALSA-.lock
        fi
        # Disable user from logging in via ssh and nx
        /usr/sbin/usermod -s /usr/sbin/nologin $user >> /dev/null 2>&1
        /usr/NX/bin/nxserver --userdel $user >> /dev/null 2>&1
    fi;
done
