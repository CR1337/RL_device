#!/bin/sh

docker run --name rl_device -d -p 5000:5000 --device /dev/i2c-1 --env-file .env --rm cr1337:rl_device