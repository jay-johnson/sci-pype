#!/bin/bash

redis-cli -p 16001 sentinel get-master-addr-by-name redis-cluster
