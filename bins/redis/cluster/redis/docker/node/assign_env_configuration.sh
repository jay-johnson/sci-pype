#!/bin/bash

source /opt/tools/bash-common.sh .

log="/tmp/container-assignment.log"
echo "" > $log

configdir="${ENV_CONFIGURABLES_DIR}/*.conf"
etcdir="${ENV_ETC_DIR}/*/*"

lg "Setting Configurables: ${configdir} " >> $log
lg "Setting etc: ${etcdir} " >> $log
 
###########################################################################
#
# ENV Variable Assignments
#
###########################################################################

list=`env | grep "ENV_"`
for envvar in $list
do
    key=`echo $envvar | sed -e 's|=| |g' | awk '{print $1}'`
    value=`echo $envvar | sed -e 's|.*=||g'`
    sed -i "s|$key|$value|g" $etcdir
    sed -i "s|$key|$value|g" $configdir
done

###########################################################################
#
# Common Host Setup
#
###########################################################################

function setup_cronjobs {

    echo "Creating new crontab file" >> $log

    cat <<EOF > ./newcron

#   
# *    *    *    *    *  command to be executed
# ┬    ┬    ┬    ┬    ┬
# │    │    │    │    │
# │    │    │    │    │
# │    │    │    │    └───── day of week (0 - 7) (0 or 7 are Sunday, or use names)
# │    │    │    └────────── month (1 - 12)
# │    │    └─────────────── day of month (1 - 31)
# │    └──────────────────── hour (0 - 23)
# └───────────────────────── min (0 - 59)

# log rotate
11     *    *    *    * /usr/sbin/logrotate /etc/logrotate.conf >/dev/null 2>&1
0,5,10,15,20,25,30,35,40,45,50,55,57      *    *    *    * /usr/bin/updatedb

EOF

    echo "" >> ./newcron
    crontab -l >> ./newcron

    crontab ./newcron
    rm ./newcron
}

function setup_rsyslog {
    echo '$SystemLogRateLimitInterval 1'  >> /etc/rsyslog.conf
    echo '$SystemLogRateLimitBurst 50000' >> /etc/rsyslog.conf
    echo '*.debug                  /var/log/messages.debug' >> /etc/rsyslog.conf

    # This prevents ami's logging to the terminal
    sed -i 's/\*.emerg/#\*.emerg/g' /etc/rsyslog.conf
    service rsyslog restart
}

function setup_logrotate {

    echo "Overwriting the /etc/logrotate.conf" >> $log

    cat <<EOF > /etc/logrotate.conf
# see "man logrotate" for details
# rotate log files weekly
weekly

# keep 4 weeks worth of backlogs
rotate 4

create

# dateext

compress

include /etc/logrotate.d

# no packages own wtmp and btmp -- we'll rotate them here
/var/log/wtmp {
    monthly
    create 0664 root utmp
    minsize 1M
    rotate 1
}

/var/log/btmp {
    missingok
    monthly
    create 0600 root utmp
    rotate 1
}

# system-specific logs may be also be configured here.

EOF


    echo "Overwriting the /etc/logrotate.d/syslog" >> $log

    cat <<EOF > /etc/logrotate.d/syslog

/var/log/cron
/var/log/maillog
/var/log/secure
/var/log/spooler
{
    sharedscripts
    postrotate
    /bin/kill -HUP \`cat /var/run/syslogd.pid\` 2> /dev/null || true
    endscript
}

/var/log/messages
/var/log/messages.debug
{
    rotate 4
    compress
    size=50M
    sharedscripts
    postrotate
    /bin/kill -HUP \`cat /var/run/syslogd.pid\` 2> /dev/null || true
    endscript
}

EOF

}

function setup_socket_recycling {

    echo "Setting up the systcl for socket recycling" >> $log

    echo "net.ipv4.tcp_tw_recycle = 1" >> /etc/sysctl.conf
    echo "net.ipv4.tcp_tw_reuse = 1" >> /etc/sysctl.conf
    echo "net.ipv4.ip_local_port_range = 1024 65535" >> /etc/sysctl.conf
    echo "" >> /etc/sysctl.conf

    echo "Refreshing systcl -p"

    /sbin/sysctl -p

    echo "Done Setting up the systcl for socket recycling" >> $log
}


# Setup the rsyslog
echo "Setting up rsyslog" >> $log
setup_rsyslog

# Setup the logrotate
echo "Setting up log rotation" >> $log
setup_logrotate

# Setup the cronjobs:
echo "Setting up cronjobs" >> $log
setup_cronjobs

# setup the recycling for /etc/sysconfig
echo "Setting up system socket recycling for active connectors" >> $log
setup_socket_recycling

exit 0 

