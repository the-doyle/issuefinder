from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import FormView
from fitz.fitz import PDF_PERM_PRINT_HQ
from .functions import find_issues
import logging
import os
from django.core.files.storage import default_storage
import json
import pandas as pd
from django.http import FileResponse, Http404
import snowflake.connector
from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine
import datetime

logger = logging.getLogger(__name__)

import pandas as pd

def index(request) :

    if os.getcwd() != '/IssueFinder':
        os.chdir('..')

    return render (request, 'findissues/index.html')

def about(request) :
    return render (request, 'findissues/about.html')

def results(request) :
    if request.method == 'POST':

        if os.getcwd() != '/IssueFinder':
            os.chdir('..')

        files = request.FILES.getlist('files') #collect files from form

        user_search_raw = request.POST.get('user_search')
        user_search = [x.strip() for x in user_search_raw.split(',')]

        for f in files:
            if not default_storage.exists(f.name):
                default_storage.save(f.name, f)

        if not user_search_raw == "":
            keywords = user_search
        else:
            keywords = []

        if request.POST.get('s-warranty'):
            keywords.append('warranty')
        if request.POST.get('s-repurchase'):
            keywords.append('repurchase')
        if request.POST.get('s-fob'):
            keywords.append('fob')
        if request.POST.get('s-obligation'):
            keywords.append('obligation')
        if request.POST.get('s-guarantee'):
            keywords.append('guarantee')
        if request.POST.get('s-shipping'):
            keywords.append('shipping')
        if request.POST.get('s-price-protection'):
            keywords.append('price protection')
        if request.POST.get('s-price'):
            keywords.append('price')
        if request.POST.get('s-termination'):
            keywords.append('termination')


        #send keywords to snowflake
        topics_list = []
        datetime_list = []
        document_type = request.POST.get('doc_type')

        for x in range(0, len(keywords)):
            topics_list.append(document_type)
            datetime_list.append(datetime.datetime.now())
            print(x)

        keywords_df = pd.DataFrame({'keywords':keywords, 'topics': topics_list, 'ts': datetime_list})

        try:
            engine = create_engine(URL(
                account = 'connorgroup.west-us-2.azure',
                user = 'CG_ETL_USER',
                password = 'a!1029rad',
                database = 'RAD_DB',
                schema = 'RAD_SCHEMA',
                warehouse = 'RAD_WH',
                role='CG_SYSADMIN',
            ))
        except:
            print('engine failed')

        try:
            connection = engine.connect()
            keywords_df.to_sql('ISSUEFINDER_KEYWORDS', engine, if_exists='append', index=False)
            connection.close()
            engine.dispose()
        except:
            print('something else failed')

        data, message, raw_df, scanned_docs, data_ocr, df_ocr = find_issues(files, "./", keywords)

        value_counts = raw_df['ISSUE'].value_counts()
        df = value_counts.to_frame()
        df['term'] = df.index
        if len(df) > 0:
            df['term_no_whitespace'] = df['term'].str.replace(' ', '')

        json_records = df.reset_index().to_json(orient ='records')
        issues_list = []
        issues_list = json.loads(json_records)

        scanned_docs_exist = "No"
        if df_ocr.size > 0:
            value_counts = df_ocr['ISSUE'].value_counts()
            df = value_counts.to_frame()
            df['term'] = df.index
            if len(df) > 0:
                df['term_no_whitespace'] = df['term'].str.replace(' ', '')
                scanned_docs_exist = "Yes"
            json_records = df.reset_index().to_json(orient ='records')
            issues_list_ocr = []
            issues_list_ocr = json.loads(json_records) 
        else:
            issues_list_ocr = ""

        #add a column for how many documents surfaced an issue in the result set

        context = {
            'data': data,
            'issues': issues_list,
            'message' : message,
            'scanned_docs_exist': scanned_docs_exist,
            'scanned_docs': scanned_docs,
            'scanned_docs_len': len(scanned_docs),
            'data_ocr': data_ocr,
            'issues_ocr': issues_list_ocr,
        }

        return render (request, 'findissues/results.html', context)

    else:
        return render (request, 'findissues/index.html')

def document(request, name, page) :
    if os.getcwd() == '/IssueFinder/findissues':
        os.chdir('..')
        os.chdir('media')

    # if page == 1000:
    #     docker_path = name
    # elif page == "1000":
    #     docker_path = name
    # else:
    docker_path = 'modified_' + name


    # with open(docker_path, 'rb') as pdf:
    #     response = HttpResponse(pdf.read(), content_type='application/pdf')
    #     response['Content-Disposition'] = 'inline;filename=' + docker_path
    #     return response

    try:
        return FileResponse(open(docker_path, 'rb'), content_type='application/pdf')
    except FileNotFoundError:
        raise Http404()

    


