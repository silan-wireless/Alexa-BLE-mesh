# Alexa-esp32freeRTOS-EFR32BG13-Bluetooth-mesh-project
![image](https://github.com/sheldon123z/Alexa-esp32freeRTOS-EFR32BG13-Bluetooth-mesh-project/blob/master/project.png)

# Instructions:
This project uses AWS to construct a message flow from Alexa server -> AWS lambda -> AWS IOT Core -> ESP32 AWS FreeRtos -> EFR32 local bluetooth network   
Therefore the cross platform message communication could be done 
This repo is just for the lambda function programming, other part of the project please refernce my other repositories 

For the lambda function, please reference [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/getting-started-create-function.html)

For the AWS IoT Core, please reference [AWS IoT](https://docs.aws.amazon.com/iot/latest/developerguide/what-is-aws-iot.html)

For Alexa Skill interfaces please reference [Alexa Skills Kit](https://developer.amazon.com/en-US/docs/alexa/quick-reference/smart-home-skill-quick-reference.html)

### Serveral things need to look for this project
* How to set up your lambda function account with IAM permission 

* How to deploy a lambda function to your choosen lambda server [[preparing your code for AWS lambda](https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit-sdk-for-python/develop-your-first-skill.html#full-source-code)]

* How to connect lambda to Alexa server

* How to connect lambda to AWS IoT core 


Also, to utilize this project, the basic knowledge of ESP32 and EFR32 series need to be understood.  
  
For learning ESP32 [ESP32 idf programming guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/index.html)

For learning EFR32 series please reference Silicon labs official website [Silicon Labs](https://www.silabs.com/)

It is possible to use ESP32 only to reproduce this project, please reference ESP32 IDF framework BLE-mesh section aforementioned 

## Material Used in this project:
* ESP32 DevKitC * 1
* Silicon Labs WSTK MG21 * 2
* Silicon Labs WSTK BG13 * 1
* Wires

