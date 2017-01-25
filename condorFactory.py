def simpleJdl(scriptName):
  return """universe = vanilla
Executable = %s 
Should_Transfer_Files = YES
WhenToTransferOutput = ON_EXIT
Notification = Error
 
Output = condorLogs/log.%s.stdout
Error = condorLogs/log.%s.stderr
Log = condorLogs/log.%s.condorlog

Queue 1
""" % (scriptName, scriptName, scriptName, scriptName)

def simpleScript(incantation, pwd):
  return """#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd %s
eval `scramv1 runtime -sh`
%s""" % ( pwd, incantation )

