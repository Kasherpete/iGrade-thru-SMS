import time
from shutil import rmtree
import credentials
import igrade_lib
import requests
import fitz
import pytextnow
from PIL import Image
from io import BytesIO
from os import remove, makedirs, mkdir, fsencode, listdir
import docx2pdf
from html2image import Html2Image

# init
client = pytextnow.Client(username=credentials.get_username(), sid_cookie=credentials.get_sid(), csrf_cookie=credentials.get_csrf())


# definitions


def ask(content, msg, timeout=60, default="", advanced=False):

    timer_timeout = time.perf_counter()
    msg.send_sms(content)

    while time.perf_counter() - timer_timeout <= timeout:

        time.sleep(1)
        new_messages = client.get_unread_messages()

        for message in new_messages:
            if message.number == message.number:

                message.mark_as_read()
                if advanced:
                    return message
                else:
                    return message.content

    # timeout error messages

    time.sleep(1)
    if default != "":

        msg.send_sms(f'ERROR:TIMEOUT. User took too long to respond. Default response: {default}.')

    else:

        msg.send_sms("ERROR:TIMEOUT. User took too long to respond. Please use command again to retry.")

    return default


def send_html(content, msg):

    # specify size. broken in chromium rn
    size = (1280, 720)
    hti = Html2Image(size=size)
    hti.size = size

    background_color = 'white'

    # define CSS styles
    hti.screenshot(html_str=content, size=size, css_str=f'''
    
    body {{background: {background_color};}}

    html *
    {{
       font-family: Arial !important;
       }}

    pre {{
      padding: 10px;
      background-color: #f8f8f8;
      border: 1px solid #ccc;
      font-size: 14px;
      line-height: 1.5;
      overflow-x: auto;
      border-radius: 5px;
      margin-bottom: 20px;
    }}

    blockquote {{
      margin: 0 0 10px;
      padding: 10px 20px;
      border-left: 5px solid #ccc;
      font-size: 14px;
      line-height: 1.5;
      background-color: #f8eaf2;
      border-left: 10px solid #d83f6a;
      margin: 20px;
      padding: 10px;
    }}
    
    table {{
  border-collapse: collapse;
  width: 100%;
  font-family: Arial, sans-serif;
  font-size: 14px;

}}

th {{
  background-color: #007bff;
  color: #ffffff;
  font-weight: bold;
  padding: 8px;
  text-align: left;
}}

th:first-child {{
  border-top-left-radius: 5px;
}}

th:last-child {{
  border-top-right-radius: 5px;
}}

th:not(:last-child) {{
  border-right: 1px solid #ffffff;
}}

tr:nth-child(even) {{
  background-color: #f2f2f2;
}}

td {{
  padding: 8px;
  border-bottom: 1px solid #dddddd;
}}

td:first-child {{
  border-left: 1px solid #dddddd;
}}

td:last-child {{
  border-right: 1px solid #dddddd;
}}
    
    ''')

    # send html as png
    msg.send_mms('screenshot.png')
    remove('screenshot.png')


def convert_pdf(file_path, download_path):


    # Open the PDF file

    with fitz.open(file_path) as doc:
        page = doc[0]

        # Render the page as a pixmap and convert it to a PNG image
        pix = page.get_pixmap()

        # convert bytes to PNG
        width, height, raw_image = pix.width, pix.height, pix.samples
        img = Image.frombytes("RGB", (width, height), raw_image)

        # Save the PNG image to a buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        # Write the buffer to a file
        with open(download_path.split('.')[0] + '.png', "wb") as f:
            f.write(buffer.getvalue())


def convert_docx(input_file, output_file):

    # Convert DOCX/DOC file to PDF
    pdf_file = output_file.split('.')[0] + '.pdf'
    docx2pdf.convert(input_file, pdf_file)


    # Convert PDF file to PNG images
    convert_pdf(input_file, output_file.split('.')[0] + '.png')

    # Delete the temporary PDF file
    remove(pdf_file)


def start(msg):


    msg.send_sms('Fetching grades. This may take a while...')
    print('Fetching Grades...')

    # client initialization
    igrade_client = igrade_lib.Client(credentials.get_igrade_username(), credentials.get_igrade_pwd())


    # code

    try:  # if dir exists
        rmtree("files")
    except FileNotFoundError:
        pass

    makedirs("files/download")
    mkdir("files/finish")

    # get assignments
    user_response = ask('would you like to get upcoming assignments or problematic assignments? Respond with 1 or 2.', msg, default='2')
    if user_response == '2':
        title = "Problematic Assignments"
        assignments = igrade_client.get_problematic_assignments()

    elif user_response == '1':
        title = "Upcoming Assignments"
        assignments = igrade_client.get_upcoming_assignments()

    else:
        title = "Problematic Assignments"
        assignments = igrade_client.get_upcoming_assignments()

    table = [['Assignment:', 'Grade:', 'Semester:', 'Assigned:', 'Class:']]

    # for each assignment
    for assignment in assignments:
        table.append([assignment['assignment'], assignment['current_grade'], assignment['semester'], assignment['assigned'], assignment['class']])

        # for each file in assignment
        for file in assignment['assignments']:

            # get file data
            response = requests.get(file['link'])
            file_path = f'files/download/{file["name"]}'
            new_file_path = f'files/finish/{file["name"]}'

            # Open a file and write the contents of the response to it
            with open(file_path, "wb") as f:
                f.write(response.content)

            # convert files
            if file_path.split('.')[1] == 'pdf':
                print('converting pdf...')
                convert_pdf(file_path, new_file_path)

            elif file_path.split('.')[1] == 'doc' or file_path.split('.')[1] == 'docx':
                print('converting docx...')
                convert_docx(file_path, new_file_path)

            elif file_path.split('.')[1] == 'jpg' or file_path.split('.')[1] == 'png' or file_path.split('.')[1] == 'jpeg':
                with open(file_path, 'w') as f:
                    file_data = f.read()


    # send files
    directory = fsencode('files/finish')

    # for i in range(30):  # used to test size limits ONLY FOR TESTING
    #     table.append(['5', '6', '7', '8', '5'])

    # ---CREATE HTML--- #

    # assignments - header

    html = f"""
        <h1 id="heading-1">{title}</h1>
        <h2 id="heading-2">Your assignments:</h2>
        
        <table>
        <thead>
        <tr>
        <th>{table[0][0]}</th>
        <th>{table[0][1]}</th>
        <th>{table[0][2]}</th>
        <th>{table[0][3]}</th>
        <th>{table[0][4]}</th>
        </tr>
        </thead>"""

    # assignments - actual data
    add_end_tag = True
    i = 0
    for j in table[1:]:
        html += f"""<tbody>
        <tr>
        <td>{j[0]}</td>
        <td>{j[1]}</td>
        <td>{j[2]}</td>
        <td>{j[3]}</td>
        <td>{j[4]}</td>
        </tr>
        </tbody>"""
        i += 1
        if i == 5:  # IF OVER 5 ASSIGNMENTS. change when lower size screenshot can be taken
            add_end_tag = False
            html += '</table>'
            html += '\n<p><b><i><mark>Continued...</mark></i></b><p><hr>'
            break

    if add_end_tag:  # if tag has not been added yet
        html += '</table><hr>'


    # ---GET GRADES--- #
    grades = igrade_client.get_percentage_grades()

    # table - header
    html += f"""
        <h2 id="heading-2">Your Classes:</h2>
    
        <table>
        <thead>
        <tr>
        <th>Class Name:</th>
        <th>Teacher:</th>
        <th>S1:</th>
        <th>S2:</th>
        <th>Total:</th>
        </tr>
        </thead>"""


    # table - actual data
    for i in grades:
        try:  # sometimes an empty dict will occur
            html += f"""<tbody>
            <tr>
            <td>{i['name']}</td>
            <td>{i['teacher']}</td>
            <td>{i['s1']}</td>
            <td>{i['s2']}</td>
            <td>{i['total']}</td>
            </tr>
            </tbody>"""
        except:
            pass
    html += '</table>'


    # send overview
    send_html(html, msg)

    # send assignments
    for file in listdir(directory):
        msg.send_mms(f'files/finish/{file.decode("utf-8")}')
        time.sleep(5)

    rmtree("files")

