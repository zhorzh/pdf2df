from tabula import read_pdf
import PyPDF2
import re
from pandas import DataFrame, concat
from datetime import datetime
import csv

# set input and output folders
INPUT_FOLDER = '/home/jovyan/work/INPUT/'
OUTPUT_FOLDER = '/home/jovyan/work/OUTPUT/'

# set PDF filename with initial data
filename = INPUT_FOLDER + 'signagnd_2018-10-28.pdf'

# read text from PDF
pdfReader = PyPDF2.PdfFileReader(open(filename, 'rb'))

# read PDF page by page
number_of_pages = pdfReader.numPages
pages = []
page = 7
for page in range(number_of_pages):
    # get title and date from the page header
    text = pdfReader.getPage(page).extractText()
    title = re.search('OKLAHOMA(.*) \(', text[:200]).group(1) or ''
    date = re.search('DATE:(.*)TIME:', text).group(1) or ''
    date = str(datetime.strptime(date, "%B %d, %Y").date())

    # parse table data from the same page
    original = read_pdf(filename, pages=page)

    # remove empty rows
    rows = original.fillna(method='ffill')
    rows['docket'] = title
    rows['date'] = date
    rows['type'] = ''
    rows['cause_num'] = ''

    # split the column 'Cause Number' into 'type' and 'cause_num'
    rows['type'], rows['cause_num'] = rows['Cause Number'].str.split(' ', 1).str

    # merge the rows
    grouped = rows.groupby('cause_num')
    rows = grouped.agg({
        'docket': 'first',
        'date': 'first',
        'type': 'first',
        'cause_num': 'first',
        'Applicant/Respondent/Staff Att.': 'first',
        'Order Descript/Relief/Title': '\n'.join,
        'County': 'first',
        'Pro.': 'first'})

    # rename the columns
    rows = rows.rename(columns={'Applicant/Respondent/Staff Att.': 'applicant',
                                'Order Descript/Relief/Title': 'order_descr',
                                'County': 'county',
                                'Pro.': 'pro'})

    # check description if exists, or fill with empty cell
    rows['order_desc_1'] = rows['order_descr'].str.split('\n').str[0]
    rows['order_desc_2'] = rows['order_descr'].str.split('\n').str[1]
    rows['order_desc_3'] = rows['order_descr'].str.split('\n').str[2]
    rows['order_desc_4'] = rows['order_descr'].str.split('\n').str[3]
    rows['order_desc_5'] = rows['order_descr'].str.split('\n').str[4]
    rows['order_desc_6'] = rows['order_descr'].str.split('\n').str[5]

    # remove empty cells
    rows = rows.fillna('')

    pages.append(rows)

    print('page {} is parsed successfully'.format(page + 1))

# merge all pages
result = concat(pages)

# save result to CSV file
result.to_csv(OUTPUT_FOLDER + 'result.csv', index=False)


# save SQL queries to file
openFile = open(OUTPUT_FOLDER + 'result.csv', 'r')
csvFile = csv.reader(openFile)
header = next(csvFile)
headers = map((lambda x: '`' + x + '`'), header)
insert = 'INSERT INTO Table (' + ", ".join(headers) + ") VALUES "

sql_queries = []
for row in csvFile:
    values = map((lambda x: '"'+x+'"'), row)
    sql_query = insert + "(" + ", ".join(values) + ");"
    sql_queries.append(sql_query)

openFile.close()

with open(OUTPUT_FOLDER + 'result.sql', 'w') as f:
    for sql_query in sql_queries:
        f.write("%s\n" % sql_query)
