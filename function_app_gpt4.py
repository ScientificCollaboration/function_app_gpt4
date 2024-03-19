import os
import azure.functions as func
import logging
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import azure.functions as func
import logging
from openai import AzureOpenAI
import json
import PyPDF2  
from xml.etree.ElementTree import Element, SubElement, tostring  
from xml.dom import minidom  
from openai import AzureOpenAI   
from pdfminer.high_level import extract_text_to_fp  
from pdfminer.layout import LAParams  
from io import BytesIO  
import xml.etree.ElementTree as ET  
from azure.storage.blob import BlobServiceClient, BlobClient  
from pdfminer.high_level import extract_text  
from azure.storage.blob import BlobServiceClient,ContainerClient, BlobClient
import datetime
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()


storage_account_key = "Ch0G5DBVdN8dVDJDsqMarKP8zmseACNCe6WIWcXeP2SYEExCY1rGKi4HU7FMJJ90GSePSrNdrser+ASt6JG2hA=="
storage_account_name = "aalex"
connection_string = "BlobEndpoint=https://aalex.blob.core.windows.net/;QueueEndpoint=https://aalex.queue.core.windows.net/;FileEndpoint=https://aalex.file.core.windows.net/;TableEndpoint=https://aalex.table.core.windows.net/;SharedAccessSignature=sv=2022-11-02&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2028-03-16T03:25:46Z&st=2024-03-15T19:25:46Z&spr=https,http&sig=1rmT%2FW9FBV1J4os1pfAVcmKuyiRtrLN6QAvd9ervY58%3D"
container_name = "eurogroup"



def download_blob(blob_client, destination_file):
    print("[{}]:[INFO] : Downloading {} ...".format(datetime.datetime.utcnow(),destination_file))
    with open(destination_file, "wb") as my_blob:
        blob_data = blob_client.download_blob()
        blob_data.readinto(my_blob)
    print("[{}]:[INFO] : download finished".format(datetime.datetime.utcnow()))  


# Assuming your Azure connection string environment variable set.
# If not, create BlobServiceClient using trl & credentials.
#Example: https://learn.microsoft.com/en-us/python/api/azure-storage-blob/azure.storage.blob.blobserviceclient 

connection_string = connection_string

blob_service_client = BlobServiceClient.from_connection_string(conn_str=connection_string) 
# create container client
container_name = 'eurogroup'
container_client = blob_service_client.get_container_client(container_name)

#Check if there is a top level local folder exist for container.
#If not, create one
data_dir ='.'
data_dir = data_dir+ "/"# + container_name
if not(os.path.isdir(data_dir)):
    print("[{}]:[INFO] : Creating local directory for container".format(datetime.datetime.utcnow()))
    os.makedirs(data_dir, exist_ok=True)
    
#code below lists all the blobs in the container and downloads them one after another
blob_list = container_client.list_blobs()
for blob in blob_list:
    print("[{}]:[INFO] : Blob name: {}".format(datetime.datetime.utcnow(), blob.name))
    #check if the path contains a folder structure, create the folder structure
    if "/" in "{}".format(blob.name):
        #extract the folder path and check if that folder exists locally, and if not create it
        head, tail = os.path.split("{}".format(blob.name))
        if not (os.path.isdir(data_dir+ "/" + head)):
            #create the diretcory and download the file to it
            print("[{}]:[INFO] : {} directory doesn't exist, creating it now".format(datetime.datetime.utcnow(),data_dir+ "/" + head))
            os.makedirs(data_dir+ "/" + head, exist_ok=True)
    # Finally, download the blob
    blob_client = container_client.get_blob_client(blob.name)
    download_blob(blob_client,data_dir+ "/"+blob.name)
# Initialize Azure Blob Service Client  
connection_string = "BlobEndpoint=https://aalex.blob.core.windows.net/;QueueEndpoint=https://aalex.queue.core.windows.net/;FileEndpoint=https://aalex.file.core.windows.net/;TableEndpoint=https://aalex.table.core.windows.net/;SharedAccessSignature=sv=2022-11-02&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2028-03-16T03:25:46Z&st=2024-03-15T19:25:46Z&spr=https,http&sig=1rmT%2FW9FBV1J4os1pfAVcmKuyiRtrLN6QAvd9ervY58%3D"  
blob_service_client = BlobServiceClient.from_connection_string(connection_string)  
container_name = "eurogroup"  
container_client = blob_service_client.get_container_client(container_name)    
# Define the directory containing the PDF files  
pdf_dir = '.'  # Replace with the path to your directory  #ITERATE OVER BLOB  STORAGE
  
api_base = "https://gptvision4.openai.azure.com/" ##os.getenv("AZURE_OPENAI_ENDPOINT")
api_key=  "fb4db6f8696843a5a33c1e6fd6643a03"  ##os.getenv("AZURE_OPENAI_API_KEY")
deployment_name = 'alexz'
api_version = '2023-12-01-preview'

# Initialize Azure OpenAI client  
client = AzureOpenAI(  
    api_key=api_key,  
    api_version=api_version,  
    base_url=f"{api_base}/openai/deployments/{deployment_name}/extensions",  
)  
  
def function_chatgpt4(text_content):  
    response = client.chat.completions.create(  
        model=deployment_name,  
        messages=[  
            {"role": "system", "content": "You are a helpful assistant."},  
            {"role": "user", "content": [  
                {  
                    "type": "text",  
                    "text": "Extract key information and classify issue. Print key data with issue classification in a format for XML data:"  
                },  
                {  
                    "type": "text",  
                    "text": text_content  
                }  
            ]}  
        ],  
        max_tokens=4000,  
        temperature=0.4  
    )  
    return response.choices[0].message.content  
  
def prettify(elem):  
    """Return a pretty-printed XML string for the Element."""  
    rough_string = tostring(elem, 'utf-8')  
    reparsed = minidom.parseString(rough_string)  
    return reparsed.toprettyxml(indent="  ")  
  
# Iterate over all files in the directory  
blobs_list = container_client.list_blobs()  
for blob in blobs_list:  
    if blob.name.endswith('.pdf'):  
            # Download PDF file  
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob.name)  
        #downloader = blob_client.download_blob()  
        # Convert PDF to text
        pdf_stream = BytesIO()  
        blob_client.download_blob().readinto(pdf_stream)  
  
        # Rewind the stream to the beginning  
        pdf_stream.seek(0) 
        # Open the PDF file  
         
        # Create a PDF reader object  
        pdf_reader = PyPDF2.PdfFileReader(pdf_stream)  
        text_content = ''  
  
            # Iterate over each page in the PDF  
        for page_num in range(pdf_reader.numPages):  
                # Extract text from the page  
            page = pdf_reader.getPage(page_num)  
            text_content += page.extractText()  
  
            # Process the text content with the ChatGPT function  
        chat_gpt_response = function_chatgpt4(text_content)  
  
            # Assume chat_gpt_response is XML-formatted string, parse it into an Element  
        root = Element('ChatGPTResponse')  
        root.text = chat_gpt_response  # Use the response directly in the XML  
  
        # Convert the XML structure to a pretty-printed XML string  
        xml_content = prettify(root)
for filename in os.listdir(pdf_dir):  
    if filename.endswith('.pdf'):        
        # Create a XML file path with the same name as the PDF file  
        xml_file_path = os.path.join(pdf_dir, filename.replace('.pdf', '.xml'))  
  
        # Write the XML content to the XML file  
        with open(xml_file_path, 'w', encoding='utf-8') as xml_file:  
            xml_file.write(xml_content)    
          
        print(f'Converted {filename} to XML.')  
  
print('Conversion complete.')  

for filename1 in os.listdir(pdf_dir):  
    if filename1.endswith('.xml'):
        ##blob_client.upload_blob(filename1) 
        # Optionally, upload the XML file back to Azure Blob Storage  
        output_blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename1)  
        with open(filename1, "rb") as data:  
            output_blob_client.upload_blob(data, overwrite=True)
        
  
print(f"XML file '{filename1}' created and uploaded to Blob Storage.") 

@app.blob_trigger(arg_name="myblob", path="gpt4xml",
                               connection="AzureWebJobsStorage") 
   
def gpt4xml(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob"
                f"Name: {myblob.name}"
                f"Blob Size: {myblob.length} bytes")
