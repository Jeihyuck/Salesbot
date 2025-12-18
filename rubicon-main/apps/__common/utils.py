import datetime
import math
import traceback

def convert_unparsables_to_string(data):
    if isinstance(data, dict):
        for key, value in data.items():
            try:
                if isinstance(value, datetime.datetime):
                    data[key] = value.isoformat()
                else:
                    convert_unparsables_to_string(value)
                if value is None:
                    data[key] = ''
                if isinstance(value, (int, float)):
                    if math.isnan(value):
                        data[key] = ''

            except Exception as e:
                traceback.print_exc()
    elif isinstance(data, list):
        for i in range(len(data)):
            try:
                if isinstance(data[i], datetime.datetime):
                    data[i] = data[i].isoformat()
                else:
                    convert_unparsables_to_string(data[i])
                if data[i] is None:
                    data[i] = ''
                if data[i] == 'None':
                    pass
                if isinstance(data[i], (int, float)):
                    if math.isnan(data[i]):
                        data[i] = ''
            except Exception as e:
                traceback.print_exc()