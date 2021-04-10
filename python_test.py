from jenkinsapi import api
import jenkins
import sys
import getopt
import datetime
import time


def printUsage():
  print "Example of using:"
  print "> my_jenkins --job=job-name --user=user_name --password=your_password --build"
  print "> my_jenkins --job=job-name --user=user_name --password=your_password --get_last_buildnumber"

def workerBuild(jobName, userName, password):
  print "Starting new build in queue: '%s" % jobName
  j = jenkins.Jenkins('http://acrobuild', userName, password)
  j.build_job(jobName, {'1': '1'})
  return

def workerGetLastBuildNumber(jobName, userName, password):
  j = api.Jenkins('http://acrobuild', userName, password)
  job = j.get_job(jobName)
  buildNumber = job.get_last_buildnumber()
  lastGoodBuildNumber = job.get_last_good_buildnumber()
  lastGoodBuildTime = datetime.datetime.fromtimestamp(job.get_last_good_build().get_timestamp() / 1000).strftime('%Y-%m-%d %H:%M:%S')
  state = "Ready"
  if (job.is_running()):
    state = "Runnig..."
  elif (job.is_queued()):
    state = "Queued..."
  print "'%s'=%s is %s, LastGood=%s @ %s" % (jobName, buildNumber, state, lastGoodBuildNumber, lastGoodBuildTime)
  return

def main(argv):
  #worker function
  worker = ""
  job = ""
  user = ""
  password = ""

  # parse options
  try:
    opts, args = getopt.getopt(argv, "", ["build", "get_last_buildnumber", "job=", "user=", "password="])
  except getopt.GetoptError:
     printUsage()
     sys.exit()

  # analise options
  for opt, arg in opts:
    if (opt == "--job"):
      job = arg
    elif (opt == "--user"):
      user = arg
    elif (opt == "--password"):
      password = arg
    elif (opt == "--get_last_buildnumber"):
      worker = "workerGetLastBuildNumber"
    elif (opt == "--build"):
      worker = "workerBuild"

  # call worker
  globals()[worker](job, user, password)

# main
main(sys.argv[1:])
