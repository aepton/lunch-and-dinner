import boto3
import os
import requests
import StringIO

from csv import DictReader
from datetime import datetime, timedelta

QUESTION_DATE = 'What date is this for?'
QUESTION_DINNER_ABE = "Where'd Abe eat dinner?"
QUESTION_DINNER_LIZZ = "Where'd Lizz eat dinner?"
QUESTION_LUNCH_ABE = "Where'd Abe get lunch?"
QUESTION_SEXYTIMES = 'Sexytimes?'

RESPONSE_DINNER_BOUGHT = 'Out'
RESPONSE_DINNER_FROM_HOME = 'At home'
RESPONSE_LUNCH_BOUGHT = '$$$'
RESPONSE_LUNCH_FROM_HOME = 'Brought one'


def get_data_from_spreadsheet():
    """
    Download Google spreadsheet and extract responses.
    """
    tpl = 'http://docs.google.com/feeds/download/spreadsheets/Export?key=%s&exportFormat=csv&gid=%s'
    gs_key = '19x7J5dynHq51M20EzZEjzL93t0HtjazKISeBag36PdE'
    gid = '918768616'
    response = StringIO.StringIO()
    results = []

    try:
        r = requests.get(tpl % (gs_key, gid))
    except Exception, e:
        return []
    for line in r.text.splitlines():
        response.write('%s\n' % line)
    # Seek to beginning of "file" so DictReader can run over every line
    response.seek(0)
    reader = DictReader(response)
    for line in reader:
        results.append(line)
    return results


def order_responses(data):
    dates = {}
    date_format = '%m/%d/%Y'
    for row in data:
        dates[datetime.strptime(row[QUESTION_DATE], date_format)] = {
            'lunchAbe': row[QUESTION_LUNCH_ABE],
            'dinnerAbe': row[QUESTION_DINNER_ABE],
            'dinnerLizz': row[QUESTION_DINNER_LIZZ],
            'sexytimes': row[QUESTION_SEXYTIMES]
        }
    return dates


def generate_email(data):
    date_format = '%m/%d/%Y'
    begin_date = datetime.strptime('1/1/2016', date_format)
    one_day = timedelta(days=1)
    one_week = timedelta(days=7)
    one_month = timedelta(days=30)
    counter = {'missing': 0}

    for key in ['lunchAbe', 'dinnerAbe', 'dinnerLizz', 'sexytimes']:
        counter[key] = {'all time': 0, 'this week': 0, 'this month': 0}

    current_date = begin_date
    end_date = datetime.today()
    while current_date < end_date:
        if current_date not in data:
            counter['missing'] += 1
        else:
            if data[current_date]['lunchAbe'] == RESPONSE_LUNCH_BOUGHT:
                counter['lunchAbe']['all time'] += 1
                if current_date >= datetime.today() - one_week:
                    counter['lunchAbe']['this week'] += 1
                if current_date >= datetime.today() - one_month:
                    counter['lunchAbe']['this month'] += 1
            if data[current_date]['dinnerAbe'] == RESPONSE_DINNER_BOUGHT:
                counter['dinnerAbe']['all time'] += 1
                if current_date >= datetime.today() - one_week:
                    counter['dinnerAbe']['this week'] += 1
                if current_date >= datetime.today() - one_month:
                    counter['dinnerAbe']['this month'] += 1
            if data[current_date]['dinnerLizz'] == RESPONSE_DINNER_BOUGHT:
                counter['dinnerLizz']['all time'] += 1
                if current_date >= datetime.today() - one_week:
                    counter['dinnerLizz']['this week'] += 1
                if current_date >= datetime.today() - one_month:
                    counter['dinnerLizz']['this month'] += 1
            if data[current_date]['sexytimes']:
                counter['sexytimes']['all time'] += int(data[current_date]['sexytimes'])
                if current_date >= datetime.today() - one_week:
                    counter['dinnerLizz']['this week'] += int(data[current_date]['sexytimes'])
                if current_date >= datetime.today() - one_month:
                    counter['dinnerLizz']['this month'] += int(data[current_date]['sexytimes'])
        current_date += one_day

    template = """
<p>Abe has eaten dinner out <strong>%s time%s</strong> in the last week. This month, he's eaten out %s time%s, and has done so %s time%s all year.</p>
<p>Lizz has eaten dinner out <strong>%s time%s</strong> in the last week. This month, she's eaten out %s time%s, and has done so %s time%s all year.</p>
<p>Abe has bought a lunch <strong>%s time%s</strong> in the last week, %s time%s in the last month and %s time%s all year.</p>
<p>Sexytimes have been had <strong>%s time%s</strong> in the last week, %s time%s in the last month and %s time%s this year.</p>
    """ % (
        counter['dinnerAbe']['this week'],
        's' if counter['dinnerAbe']['this week'] >= 2 else '',
        counter['dinnerAbe']['this month'],
        's' if counter['dinnerAbe']['this month'] >= 2 else '',
        counter['dinnerAbe']['all time'],
        's' if counter['dinnerAbe']['all time'] >= 2 else '',
        counter['dinnerLizz']['this week'],
        's' if counter['dinnerLizz']['this week'] >= 2 else '',
        counter['dinnerLizz']['this month'],
        's' if counter['dinnerLizz']['this month'] >= 2 else '',
        counter['dinnerLizz']['all time'],
        's' if counter['dinnerLizz']['all time'] >= 2 else '',
        counter['lunchAbe']['this week'],
        's' if counter['lunchAbe']['this week'] > 2 else '',
        counter['lunchAbe']['this month'],
        's' if counter['lunchAbe']['this month'] > 2 else '',
        counter['lunchAbe']['all time'],
        's' if counter['lunchAbe']['all time'] > 2 else '',
        counter['sexytimes']['this week'],
        's' if counter['sexytimes']['this week'] > 2 else '',
        counter['sexytimes']['this month'],
        's' if counter['sexytimes']['this month'] > 2 else '',
        counter['sexytimes']['all time'],
        's' if counter['sexytimes']['all time'] > 2 else ''
    )
    return template


def send_email(email_body, to_addresses=['abraham.epton@gmail.com']):
    client = boto3.client(
        'ses',
        aws_access_key_id=os.getenv('ABE_AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('ABE_AWS_SECRET_ACCESS_KEY'),
        region_name='us-east-1')
    response = client.send_email(
        Source='abraham.epton@gmail.com',
        Destination={
            'ToAddresses': to_addresses,
            'CcAddresses': [],
            'BccAddresses': []
        },
        Message={
            'Subject': {
                'Data': 'Lunch and dinner update',
                'Charset': 'utf8'
            },
            'Body': {
                'Text': {
                    'Data': email_body,
                    'Charset': 'utf8'
                },
                'Html': {
                    'Data': email_body,
                    'Charset': 'utf8'
                }
            }
        },
        ReplyToAddresses=[
            'abraham.epton@gmail.com',
        ]
    )


if __name__ == '__main__':
    send_email(generate_email(order_responses(get_data_from_spreadsheet())))
