#!/bin/bash

curpip=pip2

if [[ -e /venv/bin/pip ]]; then
    curpip=/venv/bin/pip
fi

pushd ${install_dir} >> /dev/null

date
echo "Uninstalling XGBoost"
${curpip} uninstall -y xgboost

if [[ -e "${install_dir}/xgboost" ]]; then
    pushd ${install_dir}/xgboost
    echo "Updating repo: ${install_dir}/xgboost"
    git pull
    popd
else
    echo "Cloning repo: ${install_dir}/xgboost"
    git clone --recursive https://github.com/dmlc/xgboost.git
fi

echo "Installing XGBoost"
cd xgboost  
./build.sh 
${curpip} install -e python-package
last_status=$?
if [[ "${last_status}" != "0" ]]; then
    echo "Failed to Install xgboost"
    exit 1
fi

test_installed=$(${curpip} list | grep "xgboost" | wc -l)
if [[ "${test_installed}" == "0" ]]; then
    echo "Did not find ${curpip} for xgboost"
    exit 1
fi

echo "Done installing xgboost"

exit 0
