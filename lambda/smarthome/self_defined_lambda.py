
import boto3
import json
from .alexa.skills.smarthome import AlexaResponse

iot_client = boto3.client('iot-data','us-east-1')
aws_dynamodb = boto3.client('dynamodb')


def lambda_handler(request, context):

    # Dump the request for logging - check the CloudWatch logs
    print('lambda_handler request  -----')
    jrequest = json.dumps(request)
    print(jrequest)

    if context is not None:
        print('lambda_handler context  -----')
        print(context)

    # Validate we have an Alexa directive
    if 'directive' not in request:
        aer = AlexaResponse(
            name='ErrorResponse',
            payload={'type': 'INVALID_DIRECTIVE',
                     'message': 'Missing key: directive, Is the request a valid Alexa Directive?'})
        return send_response(aer.get())

    # Check the payload version
    payload_version = request['directive']['header']['payloadVersion']
    if payload_version != '3':
        aer = AlexaResponse(
            name='ErrorResponse',
            payload={'type': 'INTERNAL_ERROR',
                     'message': 'This skill only supports Smart Home API version 3'})
        return send_response(aer.get())

    # Crack open the request and see what is being requested
    name = request['directive']['header']['name']
    namespace = request['directive']['header']['namespace']

    # Handle the incoming request from Alexa based on the namespace

    if namespace == 'Alexa.Authorization':
        if name == 'AcceptGrant':
            # Note: This sample accepts any grant request
            # In your implementation you would use the code and token to get and store access tokens
            grant_code = request['directive']['payload']['grant']['code']
            grantee_token = request['directive']['payload']['grantee']['token']
            aar = AlexaResponse(namespace='Alexa.Authorization', name='AcceptGrant.Response')
            return send_response(aar.get())



#############################define control directive responses for different directives######################################
    if namespace == 'Alexa.Discovery':
        if name == 'Discover':
            adr = AlexaResponse(namespace='Alexa.Discovery', name='Discover.Response')
            #create capability part for the response
            adr = create_discover_response(adr)             
            return send_response(adr.get()) 
    #response for turnOn/turnOff directives
    if namespace == 'Alexa.PowerController':
        return respond_powerControl_dir(request)

    #response for set color directive
    if namespace == 'Alexa.ColorController':
        return respond_colorControl_dir(request)
    
    if namespace == 'Alexa.BrightnessController':
         return respond_brightnessControl_dir(request)
     
    #respond to lock controller directive
    if namespace == 'Alexa.LockController':
        return respond_lockContro_dir(request)
    if namespace == 'Alexa.ColorTemperatureController':
        return respond_colorTemperatureControl_dir(request)

    # Report response function for responding alexa report directive
    if namespace == 'Alexa': 
        if name == 'ReportState':
            return respond_reportState_dir(request)
       


def send_response(response):
    # TODO Validate the response
    print('lambda_handler response -----')
    print(json.dumps(response))
    return response


def set_device_state(endpoint_id, state, value):
    attribute_key = state + 'Value'
    response = aws_dynamodb.update_item(
        TableName='smartHome',
        Key={'Item ID': {'S': endpoint_id}},
        AttributeUpdates={attribute_key: {'Action': 'PUT', 'Value': {'S': value}}})

    print(response)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False
    
#delete thingshadow for testing
def delete_thingshadow(thing_name_id):
    
    response = iot_client.delete_thing_shadow(
        thingName=thing_name_id)

def update_thing_shadow(thing_name_id, **kwargs):
    
    jstring = json.dumps(
        {   "state" : 
            {
                "desired": {
                    "Lights" :{ 
                        "thing name":thing_name_id,
                        "device info": kwargs.get('device_info','default information'),
                        "powerOn":kwargs.get('powerOn','ON'),
                        "brightness":kwargs.get('brightness',55),
                        "value":kwargs.get('color',{'hue': 0,'saturation':1,'brightness':1 }),
                        "colorTemperatureInKelvin":kwargs.get('colorTemperatureInKelvin',3000),
                        "property3" : kwargs.get('property3', {'default property3': 0 }),
                        kwargs.get('deleteDesired','delete') :None
                        },
                    "Switch":{
                        "Switch value":kwargs.get("switch_value","OFF") 
                        },
                    "Lock":{
                        "Lock value": kwargs.get('lock_value','LOCKED')
                        }
                },
                "reported": {
                    "Lights" :{ 
                        "thing name":thing_name_id,
                        "device info": kwargs.get('device_info','default information'),
                        "powerOn":kwargs.get('powerOn','ON'),
                        "brightness" : kwargs.get('brightness',70),
                        "value" : kwargs.get('color',{'hue': 300,'saturation':0.7201,'brightness':0.6523 }),
                        "colorTemperatureInKelvin":kwargs.get('colorTemperatureInKelvin',3000),
                        "property3" : kwargs.get('property3', {'default property3': 0 }),
                        kwargs.get('deleteDesired','delete') :None
                    },
                    "Switch":{
                        "Switch value":kwargs.get("switch_value","OFF") 
                    },
                    "Lock":{
                        "Lock value": kwargs.get('lock_value','LOCKED')
                    }
                }
            }
        }
    )    
    #comment this line if not need to clean the thingshadow
    # delete_thingshadow("sample-switch")
    
    #update iot thing shadow
    #response = iot_client.update_thing_shadow(thingName = thing_name_id, payload = jstring)
    
    response = iot_client.update_thing_shadow(thingName = thing_name_id,payload = jstring)

    #check if the update successful
    #get the streamingBody object
    streamingBody = response["payload"]
    print(streamingBody);

    #transfer streamingbody object to dictionary type
    Dic_strbody = json.loads(streamingBody.read())
    #TODO need to add check conditions below
    return True
    
    
def get_thing_shadow_dic(endpoint_id):

    response = iot_client.get_thing_shadow(thingName = "esp32")
    
   #response = iot_client.get_thing_shadow(thingName = "esp32")
    #get the streamingBody object
    streamingBody = response["payload"]
    #transfer streamingbody object to dictionary type
    Dic_strbody = json.loads(streamingBody.read())
    return Dic_strbody


def respond_colorControl_dir(request):
    
    endpoint_id = request['directive']['endpoint']['endpointId']
    correlation_token = request['directive']['header']['correlationToken']
    token = request['directive']['endpoint']['scope']['token']
    name = request['directive']['header']['name']
    #get directive specific values
    
    hue = request['directive']['payload']['color']['hue']
    saturation = request['directive']['payload']['color']['saturation']
    brightness = request['directive']['payload']['color']['brightness']

    color_parameter = {"hue":hue, "saturation":saturation, "brightness":brightness}
    thingshadow_dic = get_thing_shadow_dic(endpoint_id = endpoint_id)
    Brightness = thingshadow_dic['state']['desired']['Lights']['brightness']
    
    #send the thing shadow and check error
    thingshadow_updated = update_thing_shadow(thing_name_id = endpoint_id, color = color_parameter,brightness = Brightness)
    if not thingshadow_updated:
        return AlexaResponse(
            name='ErrorResponse',
            payload={'type': 'ENDPOINT_UNREACHABLE', 'message': 'Unable to reach endpoint database.'}).get()

    #construct response
    ccr = AlexaResponse(
        coorelation_token = correlation_token,
        endpoint_id=endpoint_id,
        token = token)
    ccr.add_context_property(namespace ='Alexa.ColorController',name='color',value = color_parameter)
    
    return send_response(ccr.get())
    
def respond_lockContro_dir(request):
    #get information from request packet
    endpoint_id = request['directive']['endpoint']['endpointId']
    correlation_token = request['directive']['header']['correlationToken']
    token = request['directive']['endpoint']['scope']['token']
    name = request['directive']['header']['name']
    #get lock state from directive
    lock_state_value = 'LOCKED' if name == 'Lock' else 'UNLOCKED'
    
    # Check for an error when setting the state, update the thing shadow
    # state_set = set_device_state(endpoint_id=endpoint_id, state='lockState', lock_value=lock_state_value)
    
    #update thing shadow
    thingshadow_updated = update_thing_shadow(thing_name_id = endpoint_id, lock_value = lock_state_value)
    if not thingshadow_updated:
        return AlexaResponse(
            name='ErrorResponse',
            payload={'type': 'ENDPOINT_UNREACHABLE', 'message': 'Unable to reach endpoint database.'}).get()

    thingshadow_dic = get_thing_shadow_dic(endpoint_id = endpoint_id)
    lock_state_value = thingshadow_dic['state']['desired']['Lock']['Lock value']
    apcr = AlexaResponse(
        correlation_token = correlation_token,
        endpoint_id = endpoint_id,
        token = token)

    apcr.add_context_property(namespace='Alexa.LockController', name='lockState', value=lock_state_value)
    
    return send_response(apcr.get())

def respond_powerControl_dir(request):
    
    # Note: This sample always returns a success response for either a request to TurnOff or TurnOn
    endpoint_id = request['directive']['endpoint']['endpointId']
    correlation_token = request['directive']['header']['correlationToken']
    token = request['directive']['endpoint']['scope']['token']
    name = request['directive']['header']['name']
    #Get original shadow
    thingshadow_dic = get_thing_shadow_dic(endpoint_id = endpoint_id)
    
    #get the power state from the directive, the value is marked in the name section, which needs to be adapted
    power_state_value = 'OFF' if name =='TurnOff' else 'ON'

    # Check for an error when setting the state, update the thing shadow
    state_set = set_device_state(endpoint_id=endpoint_id, state='powerState', value=power_state_value)
    if(endpoint_id == 'sample-light'):
        switch_value = thingshadow_dic['state']['desired']['Switch']['Switch value']
        thingshadow_updated = update_thing_shadow(thing_name_id = endpoint_id,
                                                  powerOn = power_state_value,
                                                  switch_value=switch_value)
    elif(endpoint_id == 'sample-switch-01'):
        powerOn =  thingshadow_dic['state']['desired']['Lights']['powerOn']
        brightness =  thingshadow_dic['state']['desired']['Lights']['brightness']
        temperature =  thingshadow_dic['state']['desired']['Lights']['colorTemperatureInKelvin']
        value =  thingshadow_dic['state']['desired']['Lights']['value']
        Lock_value =  thingshadow_dic['state']['desired']['Lock']['Lock value']
        thingshadow_updated = update_thing_shadow(thing_name_id = endpoint_id,
                                                  switch_value = power_state_value,
                                                  powerOn = powerOn,
                                                  brightness=brightness,
                                                  colorTemperatureInKelvin=temperature,
                                                  value = value,
                                                  lock_value = Lock_value)

    if not (state_set and thingshadow_updated):
        return AlexaResponse(
            name='ErrorResponse',
            payload={'type': 'ENDPOINT_UNREACHABLE', 'message': 'Unable to reach endpoint database.'}).get()
        
    apcr = AlexaResponse(
        coorelation_token = correlation_token,
        endpointId=endpoint_id,
        token = token)

    apcr.add_context_property(namespace='Alexa.PowerController', name='powerState', value=power_state_value)
    
    return send_response(apcr.get())

def respond_brightnessControl_dir(request):
    # Note: This sample always returns a success response for either a request to TurnOff or TurnOn
    endpoint_id = request['directive']['endpoint']['endpointId']
    correlation_token = request['directive']['header']['correlationToken']
    token = request['directive']['endpoint']['scope']['token']
    name = request['directive']['header']['name']
    #get the brightness from the directive
    brightness_value = request['directive']['payload']['brightness']
    thingshadow_updated = update_thing_shadow(thing_name_id=endpoint_id,brightness=brightness_value)
    
    #check the operation if successful
    if not (thingshadow_updated):
        return AlexaResponse(
        name='ErrorResponse',
        payload={'type': 'ENDPOINT_UNREACHABLE', 'message': 'Unable to reach endpoint database.'}).get()
    #abtr: alexa brightness response
    abtr = AlexaResponse(
        coorelation_token = correlation_token,
        endpoint_id=endpoint_id,
        token = token)    
    abtr.add_context_property(namespace = 'Alexa.BrightnessController',name = "brightness",value = brightness_value)
    
    return send_response(abtr.get())
def respond_colorTemperatureControl_dir(request):
    print("entered color resp")
    # Note: This sample always returns a success response for either a request to TurnOff or TurnOn
    endpoint_id = request['directive']['endpoint']['endpointId']
    correlation_token = request['directive']['header']['correlationToken']
    token = request['directive']['endpoint']['scope']['token']
    name = request['directive']['header']['name']
    thingshadow_dic = get_thing_shadow_dic(endpoint_id = endpoint_id)
    temperature_value = thingshadow_dic['state']['desired']['Lights']['colorTemperatureInKelvin']
    
    if(name == "SetColorTemperature"):
        temperature_value = request['directive']['payload']['colorTemperatureInKelvin']
        print("entered if color temp")
    if(name == "IncreaseColorTemperature"):
        temperature_value+=1000
    if(name =="DecreaseColorTemperature"):
        temperature_value-=1000
        
    thingshadow_updated = update_thing_shadow(thing_name_id=endpoint_id,colorTemperatureInKelvin=temperature_value)   
    
    #check the operation if successful
    if not (thingshadow_updated):
        return AlexaResponse(
        name='ErrorResponse',
        payload={'type': 'ENDPOINT_UNREACHABLE', 'message': 'Unable to reach endpoint database.'}).get()
    #abtr: alexa brightness response
    abct = AlexaResponse(
        coorelation_token = correlation_token,
        endpoint_id=endpoint_id,
        token = token)    
    abct.add_context_property(namespace = 'Alexa.ColorTemperatureController',name = "colorTemperatureInKelvin",value = temperature_value)
    
    return send_response(abct.get())
#create state report response
#state report context property only need to modify three values: namespace(report whitch interface),name(report which attribute in
#the interface), value(the value of that attribute)   
def respond_reportState_dir(request):

    #get endpoint id eg.what is the requested endpoint
    endpoint_id = request['directive']['endpoint']['endpointId']
    #get correlation_token
    correlation_token = request['directive']['header']['correlationToken']
    #get thing shadow in dictionary form
    thingshadow_dic = get_thing_shadow_dic(endpoint_id = endpoint_id)

    StateReport = AlexaResponse(
    namespace ="Alexa", 
    name = "StateReport",
    correlation_token=correlation_token,
    endpoint_id=endpoint_id
    )
    if endpoint_id =='sample-light':
        
        #need to pay attention that the value name is the name in the shadow document, not the name from alexa directives
        #get brightness value from thing shadow packet
        
        #report power controller interface 
        StateReport.add_context_property(
            namespace='Alexa.PowerController',
            name='powerState',
            value = thingshadow_dic['state']['desired']['Lights']['powerOn']
        )
        #report color values
        hue = thingshadow_dic['state']['desired']['Lights']['value']['hue']
      
        saturation = thingshadow_dic['state']['desired']['Lights']['value']['saturation']
       
        brightness = thingshadow_dic['state']['desired']['Lights']['value']['brightness']
        color_parameter = {"hue":hue, "saturation":saturation, "brightness":brightness}
        print("parameter is:{} hue: {}".format(color_parameter,hue))
        StateReport.add_context_property_with_numbers(
            namespace = 'Alexa.ColorController',
            name = 'color',
            value=color_parameter
        )
        print("stateReport is:{} ".format(StateReport))
        #report brightness value
        StateReport.add_context_property(
            namespace = 'Alexa.BrightnessController',
            name = 'brightness',
            value = thingshadow_dic['state']['desired']['Lights']['brightness']
        )
        #report color temp
        # StateReport.add_context_property(
        #     namespace = 'Alexa.ColorTemperatureController',
        #     name = 'colorTemperatureInKelvin',
        #     value = thingshadow_dic['state']['desired']['Lights']['colorTemperatureInKelvin']
        # )
        return send_response(StateReport.get())  
        
    if endpoint_id =='sample-switch-01':
        StateReport.add_context_property(
            namespace = 'Alexa.PowerController',
            name='powerState',
            value= thingshadow_dic['state']['desired']['Switch']['Switch value']
        )
        return send_response(StateReport.get())  
    if endpoint_id =='sample-lock':
        StateReport.add_context_property(
            namespace = 'Alexa.PowerController',
            name = 'powerState',
            value = thingshadow_dic['state']['desired']['Lock']['Lock value']
        )
        StateReport.add_context_property(
            namespace = 'Alexa.EndpointHealth',
            name = 'connectivity',
            value = "OK"
        )
        return send_response(StateReport.get())  
    if endpoint_id =='esp32':
        StateReport.add_context_property(
            namespace = 'Alexa.PowerController',
            name = 'powerState',
            value = thingshadow_dic['state']['desired']['esp32']['power state']
        )
        return send_response(StateReport.get())  
        
    return send_response(StateReport.get())     

#create the discover response 
#first create the capabilities that the endpoints need 
#then add the endpoints to the response entity, and add the capability information to the endpoints
def create_discover_response(response):
    #general response
    capability_alexa = response.create_payload_endpoint_capability()
    #specific capabilities
    #power controller--turn on turn off operations
    capability_alexa_PowerController = response.create_payload_endpoint_capability(
        interface='Alexa.PowerController',
        supported=[{'name': 'powerState'}])
    #create colorcontroller capability
    capability_alexa_ColorController = response.create_payload_endpoint_capability(
        interface='Alexa.ColorController',
        supported=[{'name': 'color'}])
    #create brightnessController capability
    capability_alexa_BrightnessController = response.create_payload_endpoint_capability(
        interface='Alexa.BrightnessController',
        supported=[{'name': 'brightness'}])
    #create colortemperature capability
    capability_alexa_ColorTemperatureController = response.create_payload_endpoint_capability(
        interface='Alexa.ColorTemperatureController',
        supported=[{'name': 'colorTemperatureInKelvin'}])
    #create lock controller capability
    capability_alexa_lockcontroller = response.create_payload_endpoint_capability(
        interface='Alexa.LockController',
        supported=[{'name':'lockState'}]
    )
    capability_alexa_endpointHealth = response.create_payload_endpoint_capability(
        interface='Alexa.EndpointHealth',
        supported = [{'name':'connectivity'}]
    )
    
    #add endpoints, use the capabilities created above to construct the endpoints
    #from the created capabilities to choose the ones needed
    response.add_payload_endpoint(
        friendly_name='Sample Switch',
        endpoint_id='sample-switch-01',
        manufactureName = 'silicon labs',
        display_categories = ["SWITCH"],
        discription = 'silicon labs product', 
        capabilities=[capability_alexa, capability_alexa_PowerController])
    
    #add a smaple light
    response.add_payload_endpoint(
        friendly_name = 'Sample Light',
        endpoint_id ='sample-light',
        manufactureName = 'silicon labs',
        display_categories=["LIGHT"],
        discription = 'silicon labs product', 
        capabilities=[capability_alexa,capability_alexa_PowerController,
                        capability_alexa_ColorController,
                        capability_alexa_BrightnessController,
                        capability_alexa_ColorTemperatureController])
    
    #add a sample lock
    response.add_payload_endpoint(
        friendly_name = 'Sample Lock',
        endpoint_id ='sample-lock',
        display_categories = ["SMARTLOCK"],
        manufactureName = 'silicon labs',
        discription = 'silicon labs product', 
        capabilities=[capability_alexa,capability_alexa_lockcontroller,capability_alexa_endpointHealth])
    
    #add a sample hub
    response.add_payload_endpoint(
        friendly_name='Bluetooth Mesh Hub',
        endpoint_id='esp32',
        manufactureName = 'silicon labs',
        display_categories = ["OTHER"],
        discription = 'silicon labs product', 
        capabilities=[capability_alexa, capability_alexa_PowerController])

    return response
            

    
