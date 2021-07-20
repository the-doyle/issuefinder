import pandas as pd
import fitz
from django.core.files.storage import default_storage
import json
import os
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from array import array
from PIL import Image
import sys
import time

def find_issues(files, dest_filepath, keywords):
    # sort through and gather keywords from user input

    '''
    Authenticate
    Authenticates your credentials and creates a client.
    '''
    subscription_key = "computer vision credentials"
    endpoint = "normally go here"
    computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

    #switch into the proper directory if needed
    if os.getcwd() != '/media':
        os.chdir('media')
   
    #empty lists to store outputs
    titles = []
    page_nums = []
    issues = []
    scanned_docs = []

    titles_ocr = []
    page_nums_ocr = []
    issues_ocr = []

    #iterate through files and perform processing
    for f in files:
        with fitz.open(f.name) as doc:  
            doc.authenticate("")
            page_num = 1
            start_len = len(issues)

            for page in doc:
                doc_text = ""
                doc_text = page.get_text()
                if len(doc_text) > 500:
                    break

            if len(doc_text) < 500:
                scanned_docs.append(f)
                read_image_path = os.path.join("", f.name)
                # Open the image
                read_image = open(read_image_path, "rb")
                # Call API with image and raw response (allows you to get the operation location)
                read_response = computervision_client.read_in_stream(read_image, raw=True)
                # Get the operation location (URL with ID as last appendage)
                read_operation_location = read_response.headers["Operation-Location"]
                # Take the ID off and use to get results
                operation_id = read_operation_location.split("/")[-1]
                # Call the "GET" API and wait for the retrieval of the results
                while True:
                    read_result = computervision_client.get_read_result(operation_id)
                    if read_result.status.lower () not in ['notstarted', 'running']:
                        break
                    print('Waiting for result...')
                    time.sleep(10)

                for text_result in read_result.analyze_result.read_results:
                    for line in text_result.lines:
                        matches = [x for x in keywords if x in line.text]
                        if matches:
                            load_page = text_result.page - 1
                            page = doc.load_page(load_page) #opens page object 
                            pixmap = page.get_pixmap() #get dimensions of page in pixels 
                            page_bound = page.bound() #get dimensions of page in standard units 
                            page_width = page_bound[2] / 72 #the next four lines are conversions to standardize highlighting 
                            page_height = page_bound[3] / 72
                            ppi_width = pixmap.width / page_width
                            ppi_height = pixmap.height / page_height

                            line_text = line.text
                            text_len = len(line_text) # length of text in characters 
                            bounding_box = line.bounding_box #bounding box of line 
                            line_length_pixels = (bounding_box[2] * ppi_width) - (bounding_box[0] * ppi_width) #length of line in pixels
                            pixels_per_character = line_length_pixels / text_len
                            start_pixels = bounding_box[0] * ppi_width
                            end_pixels = bounding_box[2] * ppi_width
                            list_quads = []

                            for match in matches:

                                match_index = line_text.index(match)
                                match_len = len(match)

                                start_highlight_pixels = start_pixels + (match_index * pixels_per_character)
                                end_highlight_pixels = start_highlight_pixels + (match_len * pixels_per_character)
                           
                                aw = start_highlight_pixels
                                ah = bounding_box[1] * ppi_height
                                bw = end_highlight_pixels
                                bh = bounding_box[3] * ppi_height
                                cw = start_highlight_pixels
                                ch = bounding_box[5] * ppi_height
                                dw = end_highlight_pixels
                                dh = bounding_box[7] * ppi_height
                                
                                quad = fitz.Quad((aw, ah), (bw, bh), (cw, dh), (dw, ch))
                                list_quads.append(quad)
                            # list_quads = [quad]
                            page.add_highlight_annot(list_quads)
                            #highlight quad here 
                            for match in matches:
                                titles_ocr.append(f)
                                page_nums_ocr.append(text_result.page)
                                issues_ocr.append(match)

            else:
                for page in doc:
                    for phrase in keywords: 
                        partial = page.search_for(phrase, quads = True) # get list of text locations
                        try:
                            page.addHighlightAnnot(partial) # mark all found quads with one annotation
                        except:
                            pass
                        if len(partial) > 0:
                            titles.append(f) #store key information about each document
                            page_nums.append(page_num)
                            issues.append(phrase)

                    page_num += 1
            
            save_filename = dest_filepath + "/modified_" + f.name
            doc.save(save_filename)

    df = pd.DataFrame({
        'ISSUE': issues,
        'PDF': titles,
        'PAGE': page_nums
      })
    if df.size > 0: 
        output_message = f'IssueFinder located {int(df.size / 3)} terms in the uploaded documents'
    else: 
        output_message = 'No terms located'

    if df.size == 1:
        output_message = 'IssueFinder located 1 term in the uploaded documents'

    json_records = df.reset_index().to_json(orient ='records')
    data = []
    data = json.loads(json_records)

    if len(scanned_docs) > 0:
            
        df_ocr = pd.DataFrame({
            'ISSUE': issues_ocr,
            'PDF': titles_ocr,
            'PAGE': page_nums_ocr
        })
        json_records = df_ocr.reset_index().to_json(orient ='records')
        data_ocr = []
        data_ocr = json.loads(json_records)
    else:
        df_ocr = pd.DataFrame()
        data_ocr = ""
    
    return data, output_message, df, scanned_docs, data_ocr, df_ocr
