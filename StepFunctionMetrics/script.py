import json

import boto3
env='qa'
arn = "stepFunctionArn"

pageSize = 20
maxItems = 20

inputStartDate = 
inputEndDate = 

def lambda_handler(event, context):
    # Initialize clients
    sf_client = boto3.client('stepfunctions')

    '''
    response_act = sf_client.list_activities(maxResults=3)
    for k, v in response_act.items():
        print(k, v);
    '''    
    response_iterator = sf_client.list_executions(stateMachineArn=arn, maxResults = 5)
    # print(response_iterator)
    for exe_index, execution in enumerate(response_iterator['executions']):
        # Execution 
        exe_arn = execution['executionArn']
        exe_id = execution['name']
        exe_startTime = execution['startDate']
        exe_endTime = execution['stopDate']
        exe_status = execution['status']
        # print(execution)
        print(f"Exec-{exe_index}: {exe_id} | {exe_startTime} | {exe_endTime} | {exe_status} | Dur: {(exe_endTime - exe_startTime)}\n")
        
        response_describe_exe = sf_client.describe_execution(executionArn=exe_arn)
        #for k, v in response_describe_exe.items():
        #    print(k, v);
        print("\n")
        output = response_describe_exe["output"]
        if "ResultWriterDetails" in output:
            #print("Output", output)
            file_path = json.loads(output)["ResultWriterDetails"]["Key"]
            file_name = file_path.split("/")[0]
            print(file_name, "\n");
        '''
        response_exe_hist = sf_client.get_execution_history(
            executionArn=exe_arn,
            maxResults=4,
            reverseOrder=False,
            includeExecutionData=True
        )
        for ev in response_exe_hist['events']:
            for k,v in ev.items():
                print(k,v)
        if exe_index==2:
            break;
        '''
        response_maps = sf_client.list_map_runs(executionArn = exe_arn,  maxResults = 3)
        print("\n")

        for map_index, mapRun in enumerate(response_maps['mapRuns']):
            map_exe_arn = mapRun['executionArn']
            map_run_arn = mapRun['mapRunArn']
            mapRun_startTime = mapRun['startDate']
            mapRun_endTime = mapRun['stopDate']
            print(f"Exec-{exe_index}-Map-{map_index}: {map_run_arn.split('/')[1]}, {mapRun_startTime}, {mapRun_endTime} | Dur: {(exe_endTime - exe_startTime)}")
            
            response_map_desc = sf_client.describe_map_run(mapRunArn=map_run_arn)
            map_startTime = response_map_desc['startDate']
            map_endTime = response_map_desc['stopDate']
            map_status = response_map_desc['status']
            itemCounts = response_map_desc['itemCounts']
            success_count = itemCounts['succeeded']
            fail_count = itemCounts['failed']
            #
            print(f"Exec-{exe_index}-Map-{map_index}:{map_startTime}|{map_endTime}|{map_status}\
                  |Dur(MRPT):{(map_endTime - map_startTime)}|S:{success_count}|F:{fail_count}\n")
            #for k, v in map.items():
            #    print(k, v);
            #if map_index = 3:
            #    break;
        print("\n")
        #if exe_index == 3:
        #    break;
    
    
