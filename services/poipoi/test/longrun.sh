#!/bin/bash


NOW=$(date +%s)
LIMIT=$(expr $NOW + 3600 \* 4 )

# Args check
if [ $# -eq 1 ]
then
	LIMIT=$(expr $1 \* 60 + $NOW)
fi

echo "**************************************"
echo "You haven't speciefied any limit for the stress test. I will set 4 hours as limit. Good luck!"
echo "**************************************"

echo "Each run will have 50 parallel requests."

RUN=0
while [ $(date +%s) -lt $LIMIT ]
do
	echo "Run number $RUN"
	RES=`bash stress-test.sh info.json 50`
	if [ $RES -ne 50 ]
	then
		echo "ABORTED: RUN number $RUN has failed."
		exit -1
	else
		RUN=$(expr $RUN + 1)
	fi
	sleep 5
done
