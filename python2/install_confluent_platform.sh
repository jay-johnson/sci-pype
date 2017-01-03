#!/bin/bash

# Run as sudo for Fedora/RHEL/CentOS os's

echo "Installing key"
rpm --import http://packages.confluent.io/rpm/3.1/archive.key

echo "Installing repo file: /etc/yum.repos.d/confluent-kafka.repo"
cp ./yum-7-confluent-kafka.repo /etc/yum.repos.d/confluent-kafka.repo

echo "Cleaning yum"
yum clean all

echo "Installing Confluent Platform"
yum install -y confluent-platform-oss-2.11
last_status=$?
if [[ "${last_status}" != "0" ]]; then
    echo "Failed to Install Confluent Platform. Please see the official Confluent install guide: http://docs.confluent.io/3.1.1/installation.html#rpm-packages-via-yum"
    exit 1
else
    echo " - Installed"
fi

echo "Installing Confluent Kafka Client Dependencies"
yum install -y librdkafka1 librdkafka-devel
last_status=$?
if [[ "${last_status}" != "0" ]]; then
    echo "Failed to Install Confluent: librdkafka1 librdkafka-devel packages. Please see the official Confluent install guide: http://docs.confluent.io/3.1.1/installation.html#rpm-packages-via-yum"
    exit 1
else
    echo " - Installed"
fi

echo "Done installing Confluent Platform"

exit 0
