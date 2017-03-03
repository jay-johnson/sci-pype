log="/tmp/common.log"

export ENV_OS_TYPE="fc24"
export ENV_CORE_HOST_TYPE="local"
export ENV_CORE_DEPLOYMENT="NOCACHES"

txtund=""
txtbld=""
blddkg=""
bldred=""
bldblu=""
bldylw=""
bldgrn=""
bldgry=""
bldpnk=""
bldwht=""
txtrst=""

# check if stdout is a terminal...
if test -t 1; then
    if [[ -e /usr/bin/tput ]]; then
        # see if it supports colors...
        ncolors=$(tput colors)

        if test -n "$ncolors" && test $ncolors -ge 8; then

            txtund=$(tput sgr 0 1)          # Underline
            txtbld=$(tput bold)             # Bold
            blddkg=${txtbld}$(tput setaf 0) # Dark Gray
            bldred=${txtbld}$(tput setaf 1) # Red
            bldblu=${txtbld}$(tput setaf 2) # Blue
            bldylw=${txtbld}$(tput setaf 3) # Yellow
            bldgrn=${txtbld}$(tput setaf 4) # Green
            bldgry=${txtbld}$(tput setaf 5) # Gray
            bldpnk=${txtbld}$(tput setaf 6) # Pink
            bldwht=${txtbld}$(tput setaf 7) # White
            txtrst=$(tput sgr0)             # Reset
        fi
    fi
fi
     
dbg() {
    cdate=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${bldwht}$cdate $@ $txtrst"
    echo "$cdate $@" >> $log
}
 
inf() {
    cdate=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$cdate $@"
    echo "$cdate $@" >> $log
}
 
anmt() {
    cdate=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${bldylw}$cdate $@ $txtrst"
    echo "$cdate $@" >> $log
}

amnt() {
    cdate=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${bldylw}$cdate $@ $txtrst"
    echo "$cdate $@" >> $log
}

warn() {
    cdate=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${bldylw}$cdate $@ $txtrst"
    echo "$cdate $@" >> $log
}
 
ign() {
    cdate=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${blddkg}$cdate $@ $txtrst"
    echo "$cdate $@" >> $log
}
 
good() {
    cdate=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${bldgrn}$cdate $@ $txtrst"
    echo "$cdate $@" >> $log
}
 
green() {
    cdate=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${bldgrn}$@ $txtrst"
    echo "$cdate $@" >> $log
}
 
err() {
    cdate=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${bldred}$cdate $@ $txtrst"
    echo "$cdate $@" >> $log
}
 
lg() {
    cdate=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$cdate $@"
    echo "$cdate $@" >> $log
} 
