import json
import datetime
import boto3
import math
from dateutil.tz import tzlocal, gettz
env='qa'
arn = "yourArn"
EST = gettz('America/New_York')
pageSize = 20
#inputStartDate = datetime.datetime(2023, 10, 2, 16,0,0, 0, tzinfo=EST)
#inputEndDate = datetime.datetime(2023, 10, 2, 17, 0, 0, 0, tzinfo=EST)
def serialize_datetime(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")
    
def loadDate(inputDate, timezone):
    y,m,d,hr,mins,seconds,ms = inputDate
    return datetime.datetime(y,m,d, hr, mins, seconds,ms, tzinfo=timezone)

def getTimeInSec(inputSec):
    return datetime.timedelta(seconds=inputSec)

def convertUtcToEST(utc):
    return utc.astimezone(EST)
  
def calulateTimeDifference(ev, eventHistory):
    currTS = ev['timestamp']
    prevEventId = ev['previousEventId']
    prevEvent = [x for x in eventHistory if x["id"] == prevEventId ][0]
    #print("currEv", ev)
    #print("prevEv", prevEvent)
    prevEventTS = prevEvent['timestamp']
    #print(currTS, prevEventTS)
    diff = currTS - prevEventTS
    return diff;

def lambda_handler(event, context):
    results = []
    inputStartDate = loadDate(event["startTime"], EST)
    inputEndDate = loadDate(event["endTime"], EST)
    totalExecutions = event["totalExecutions"]
    maxResults = event["maxResults"]
    print(f"St:{inputStartDate}, Ed:{inputEndDate}")
    
    # Initialize clients
    sf_client = boto3.client('stepfunctions')

    '''
    response_act = sf_client.list_activities(maxResults=3)
    for k, v in response_act.items():
        print(k, v);
    '''    
    response_iterator = sf_client.list_executions(stateMachineArn=arn, maxResults = maxResults)
    filtered_executions = []
    print("Total Executions: ", len(response_iterator['executions']))
    for exe_index, execution in enumerate(response_iterator['executions']):
        # Execution 
        exe_status = execution['status']
        
        if exe_status != 'RUNNING':
            exe_arn = execution['executionArn']
            exe_id = execution['name']
            exe_localSt = convertUtcToEST(execution['startDate'])
            exe_localEt = convertUtcToEST(execution['stopDate'])
            #if ((exe_startTime >= inputStartDate && inputStartDate < exe_endTime) || (exe_startTime <= inputEndDate && inputEndDate >= exe_endTime)):
            #print(f"{exe_index}:{exe_id}:EXE_ST:{exe_startTime}|{exe_localSt}, IN_ED:{inputEndDate}, EXE_ET:{exe_localEt},IN_ST:{inputStartDate}")
            if exe_localSt <= inputEndDate and exe_localEt >= inputStartDate:
                filtered_executions.append(execution);
    filtered_exe_len = len(filtered_executions);
    print('Total Filter Execution:', filtered_exe_len)
    # return;
    if filtered_exe_len != totalExecutions:
        #print(f"F:{filtered_exe_len} != {totalExecutions}")
        return json.dumps({
            status:500, body: f"filtered execution didn't match with totalExecutions expected {filtered_exe_len} != {totalExecutions}"
        })
        # print(execution)
        
    for exe_index, f in enumerate(filtered_executions):
        result = {}
        exe_arn = f['executionArn']
        exe_id = f['name']
        exe_startTime = f['startDate']
        exe_endTime = f['stopDate']
        exe_status = f['status']
        result["execution"]= {'executionId': exe_id, 'startTime':exe_startTime.isoformat(), 'endTime':exe_endTime.isoformat(), 'duration':str(exe_endTime-exe_startTime)}
        response_describe_exe = sf_client.describe_execution(executionArn=exe_arn)

        opJson = json.loads(response_describe_exe["output"])
        # print(opJson)
        if opJson["ResultWriterDetails"]:
            #print("Output", output)
            file_path = opJson["ResultWriterDetails"]["Key"]
            file_name = file_path.split("/")[0]
            print(f"Exec-{exe_index}: {file_name}");
            result['file_name']=file_name
        if opJson["glueJobResponse"]:
            completedTime = opJson["glueJobResponse"]["CompletedOn"]
            startedOn = opJson["glueJobResponse"]["StartedOn"]
            glueExecutionTimeSec = opJson["glueJobResponse"]["ExecutionTime"]
            startupTimeSec = math.floor((completedTime - startedOn)/1000) - glueExecutionTimeSec
            executionPlusStartup = glueExecutionTimeSec + startupTimeSec
            glueJobKey = opJson["glueJobResponse"]["Arguments"]["--input_file_key"]
            #print(f"StartUp Time:{getTimeInSec(startupTimeSec)}|ExecutionTime:{getTimeInSec(glueExecutionTimeSec)}|Total:{getTimeInSec(executionPlusStartup)}")
            result["glueJob"]={'startUptime':str(getTimeInSec(startupTimeSec)), 'executionTime':str(getTimeInSec(glueExecutionTimeSec)), 
                                'startUpPlusExecution':str(getTimeInSec(executionPlusStartup)), 'outputFile':glueJobKey } 
            # print(f"OutputFile:{glueJobKey}")
            
    
        response_exe_hist = sf_client.get_execution_history(
            executionArn=exe_arn,
            maxResults=20,
            reverseOrder=False,
            includeExecutionData=True
        )
        eventHistory = response_exe_hist['events']
        eventDuration = {}
        for ev_idx, ev in enumerate(eventHistory):
            type = ev['type']
            evId = ev['id']
            if "ExecutionStarted" in type:
                exeStartTs = ev['timestamp']
            elif "Map" in type:
                if "Entered" in type:
                    currMapTS = ev['timestamp']
                    mapDur = currMapTS - exeStartTs
                    mapEnteredDuration = mapDur
                    prevMapTS = exeStartTs
                    #print(f"{currMapTS}==={prevMapTS}==={mapDur}")
                    prevMapTS = currMapTS
                    #print(f"{type}:{mapDur}")
                elif "Exited" in type:
                    mapExitTS = ev['timestamp']
                    mapDur += (mapExitTS - prevMapTS) - mapEnteredDuration
                    #print(f"{currMapTS}==={prevMapTS}==={mapDur}")
                    print(f"MapRunDuration:{mapDur}")
                    eventDuration["MapRunDuration"]=str(mapDur)
                else:
                    currMapTS = ev['timestamp']
                    mapDur += (currMapTS - prevMapTS)
                    #print(f"{currMapTS}==={prevMapTS}==={mapDur}")
                    #print(f"{type}:{mapDur}")
                    prevMapTS = currMapTS    
            elif "Task" in type:
                if "Entered" in type:
                    currTaskTS = ev['timestamp'];
                    taskDur = currTaskTS - mapExitTS
                    #print(f"{currTaskTS}==={mapExitTS}==={taskDur}")
                    taskEnteredDur = taskDur
                    prevTaskTS = mapExitTS
                    #print(f"{type}: {taskDur}")
                elif "Exited" in type:
                    # reset
                    currTaskTS = ev['timestamp']
                    taskDur += (currTaskTS - prevTaskTS)
                    prevTaskTS = currTaskTS
                    mapExitTS = currTaskTS
                    taskName = ev['stateExitedEventDetails']['name']
                    print(f"{taskName}: {taskDur}")
                    eventDuration[taskName]=str(taskDur)
                else:
                    currTaskTS = ev['timestamp']
                    taskDur += (currTaskTS - prevTaskTS)
                    # print(f"{type}:{taskDur}")
                    prevTaskTS = currTaskTS
        result["eventDurations"]=eventDuration
        
        response_maps = sf_client.list_map_runs(executionArn = exe_arn,  maxResults = 1)
        
        for map_index, mapRun in enumerate(response_maps['mapRuns']):
            map_exe_arn = mapRun['executionArn']
            map_run_arn = mapRun['mapRunArn']
            mapRun_startTime = mapRun['startDate']
            mapRun_endTime = mapRun['stopDate']
            # print(f"Exec-{exe_index}-Map-{map_index}: {map_run_arn.split('/')[1]}, {mapRun_startTime}, {mapRun_endTime} | Dur: {(exe_endTime - exe_startTime)}")
            
            response_map_desc = sf_client.describe_map_run(mapRunArn=map_run_arn)
            map_startTime = response_map_desc['startDate']
            map_endTime = response_map_desc['stopDate']
            map_status = response_map_desc['status']
            itemCounts = response_map_desc['itemCounts']
            success_count = itemCounts['succeeded']
            fail_count = itemCounts['failed']
            result["mapRunDuration"]=str(map_endTime - map_startTime)
            #print(f"Exec-{exe_index}-Map-{map_index}:{map_startTime}|{map_endTime}|{map_status}|Dur(MRPT):{(map_endTime - map_startTime)}|S:{success_count}|F:{fail_count}")
        results.append(result)
    print(json.dumps(results))
    return json.dumps(results) #,  default=serialize_datetime)
    #return JSON.stringify(results)

    
