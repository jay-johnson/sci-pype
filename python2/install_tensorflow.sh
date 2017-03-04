#!/bin/bash

curpip=pip2

if [[ -e /venv/bin/pip ]]; then
    curpip=/venv/bin/pip
fi

# Run as sudo for Fedora/RHEL/CentOS os's
tf_version=tensorflow-1.0.0-cp27-none-linux_x86_64.whl
pushd /tmp >> /dev/null
wget https://storage.googleapis.com/tensorflow/linux/cpu/$tf_version -O /tmp/$tf_version
if [[ ! -e "/tmp/${tf_version}" ]]; then
    echo "Failed to Download: ${tf_version}"
    exit 1
else
    echo " - Downloaded: ${tf_version}"
fi
popd >> /dev/null

echo "Installing Tensorflow: ${tf_version}"
${curpip} install --upgrade /tmp/$tf_version 
last_status=$?
if [[ "${last_status}" != "0" ]]; then
    echo "Failed to Install Tensorflow: ${tf_version}"
    exit 1
else
    echo " - Installed: ${tf_version}"
    rm -f /tmp/$tf_version
fi

test_installed=$(${curpip} list | grep "tensorflow" | wc -l)
if [[ "${test_installed}" == "0" ]]; then
    echo "Did not find ${curpip} for Tensorflow: ${tf_version}"
    exit 1
fi

echo "Done installing Tensorflow"

exit 0
