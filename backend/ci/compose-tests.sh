
#
clear

# cleanup possibly existing jobs
cleanup () {
  docker-compose -f ci/docker-compose-test.yml -p ci kill
  docker-compose -f ci/docker-compose-test.yml -p ci down --remove-orphans
  docker rmi -f $(docker images | grep "none" | awk "{print $3}")
}

# catch unexpected failures, do cleanup and output an error message
trap 'cleanup ; printf "${RED}Tests Failed For Unexpected Reasons${NC}\n"'\
  HUP INT QUIT PIPE TERM

#printenv
docker-compose -f ci/docker-compose-test.yml -p ci up --build -d # daemon, do not display container logs

if [ $? -ne 0 ] ; then
  printf "${RED}Docker Compose Failed${NC}\n"
  exit -1
fi

# wait for the tests to complete and grab the exit code
# CELERY_EXIT_CODE=`docker wait ci_tasks`
TEST_EXIT_CODE=`docker wait ci_rep_scraper`

# echo $TEST_EXIT_CODE

# print celery exit_code
# echo "Celery exit code: $CELERY_EXIT_CODE"

# output the logs for the test (for clarity)
# docker logs ci_matchservice_1
# docker logs ci_tasks
docker logs ci_rep_scraper

# colors to output results
# in red if arg passed is <> 0
# in green if arg passed is 0
# ex: print_color "test" "0" <-- outputs "test" in green
# ex: print_color "test" "1" <-- outputs "test" in red
print_color() {

  RED='\033[0;31m'
  GREEN='\033[0;32m'

  if [[ $2 -eq 0 ]]; then
    echo "${GREEN}$1\n"
  else
    echo "${RED}$1\n"
  fi

}

# inspect the output of the test and display respective message
if [[ $TEST_EXIT_CODE -eq 0 ]]; then
  print_color "Tests Passed"
else
  # override the default code
  print_color "Tests Failed"
fi

# call the cleanup fuction
cleanup

# exit the script with the same code as the test exit code
exit $TEST_EXIT_CODE
