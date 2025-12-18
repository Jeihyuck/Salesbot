import uuid
import pandas as pd
from alpha import __log
from icecream import ic
from django.db.models import F, Q
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector

from apps.rubicon_admin.models import Test_Query, Chat_Test

def create_test_query(request_dict):
    # __log.debug(request_dict)

    Test_Query.objects.create(
        case=request_dict['query']['case'],
        language=request_dict['query']['language'],
        channel=request_dict['query']['channel'],
        country=request_dict['query']['country'],
        intelligence=request_dict['query']['intelligence'],
        query=request_dict['query']['query'],
    )
    return True, None, None, {'type': 'success', 'title': 'Successfully Created', 'text' : 'Successfully added up ' + request_dict['query']['query']}

def read_test_query(request_dict):
    # __log.debug(request_dict)
    qeury = Test_Query.objects
    if 'case' in request_dict['query']:
        qeury = qeury.filter(case=request_dict['query']['case'])
    if 'language' in request_dict['query']:
        qeury = qeury.filter(language=request_dict['query']['language'])
    if 'channel' in request_dict['query']:
        qeury = qeury.filter(channel=request_dict['query']['channel'])
    if 'country' in request_dict['query']:
        qeury = qeury.filter(country=request_dict['query']['country'])
    if 'intelligence' in request_dict['query']:
        qeury = qeury.filter(intelligence=request_dict['query']['intelligence'])

                 
    item_count = qeury.count()
    items = list(qeury.order_by('-updated_on').values('id', 'case', 'language', 'channel', 'country', 'intelligence', 'query', 'created_on', 'updated_on'))
    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))
    # __log.debug(page_data)

    return True, page_data, [{'itemCount': item_count}], None


def update_test_query(request_dict):
    # __log.debug(request_dict)?
    Test_Query.objects.filter(id=request_dict['query']['id']).update(
        case=request_dict['query']['case'],
        language=request_dict['query']['language'],
        channel=request_dict['query']['channel'],
        country=request_dict['query']['country'],
        intelligence=request_dict['query']['intelligence'],
        query=request_dict['query']['query'],
    )
    return True, None, None, {'type': 'success', 'title': 'Successfully Created', 'text' : request_dict['query']['query'] + ' has updated'}


def delete_test_query(request_dict):
    # __log.debug(request_dict)
    Test_Query.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, None


def list_case(request_dict):
    qeury = Test_Query.objects
    items = list(qeury.order_by('case').values('case').distinct())

    return_list = []
    for item in items:
        return_list.append(item['case'])
    return True, return_list, None, None

def create_test_case(request_dict):
    __log.debug(request_dict)

    if request_dict['query']['selectingMethod'] == 'items':
        items = list(Test_Query.objects.filter(id__in = request_dict['query']['selected']).values('id', 'case', 'language', 'channel', 'country', 'intelligence', 'query', 'reference_response'))

    elif request_dict['query']['selectingMethod'] == 'cases':
        items = list(Test_Query.objects.filter(case__in = request_dict['query']['selectedCaseIds']).values('id', 'case', 'language', 'channel', 'country', 'intelligence', 'query', 'reference_response'))

    for item in items:
        # ic(item)
        Chat_Test.objects.create(
            test_query_id=item['id'],
            test_id=request_dict['query']['testID'],
            case=item['case'],
            language=item['language'],
            channel=item['channel'],
            country=item['country'],
            intelligence=item['intelligence'],
            query=item['query'],
            reference_response=item['reference_response'],
            tested=False
        )

    return True, None, None, {'type': 'success', 'title': 'Successfully Created', 'text' : request_dict['query']['testID'] + ' has updated'}


def translate(request_dict):
    __log.debug(request_dict)
    return True, None, None, None

def upload_query_template(request_dict):
    binary_data = request_dict['files'][0]['file']

    filename = str(uuid.uuid4()) + '.xlsx'
    file_path = '/tmp/upload/' + filename

    with open(file_path, 'wb') as f:
        f.write(binary_data)

    

    # Read the Excel file into a DataFrame
    df = pd.read_excel(file_path)

    # This assumes the first row of the Excel sheet is either headers or data you don't want to start from.
    # Using df.iloc[1:] will create a new DataFrame that starts from the second row.
    count = 0
    for index, row in df.iloc[0:].iterrows():
        count = index
        error = 'Error at row '
        try:
            Test_Query.objects.create(
                case=row.Case,
                language=row.Language,
                channel=row.Channel,
                country=row.Country,
                intelligence=row.Intelligence,
                query=row.Query,
            )
        except Exception as e:
            __log.error(f"Error at row {index}: {e}")
            error =  error + str(index) + ', '
    count = count + 1
    if error == 'Error at row ':
        return True, None, None, {'type': 'success', 'title': 'Data has uploaded', 'text' : str(count) + ' query has updated'}
    else:
        return True, None, None, {'type': 'success', 'title': 'Data has uploaded But...', 'text' : error}