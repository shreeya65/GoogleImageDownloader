import os
import requests
import zipfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import streamlit as st
import shutil


def search_and_download_images(query, num_images, api_key, cx, download_folder='images'):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'num': 50,  
        'imgSize': 'medium',
        'searchType': 'image',
        'key': api_key,
        'cx': cx,
        'fileType': 'jpg|png|gif',
    }

    downloaded_images = []
    start_index = 1

    while len(downloaded_images) < num_images and start_index <= 91:
        params['start'] = start_index
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            results = response.json()

            if 'items' not in results:
                break

            for item in results['items']:
                if len(downloaded_images) >= num_images:
                    break

                image_url = item['link']
                try:
                    img_response = requests.get(image_url, timeout=10)
                    img_response.raise_for_status()

                    file_extension = os.path.splitext(image_url)[-1].lower()
                    if file_extension not in ['.jpg', '.jpeg', '.png', '.gif']:
                        file_extension = '.jpg'

                    image_path = f"{download_folder}/image_{len(downloaded_images)+1}{file_extension}"
                    with open(image_path, 'wb') as f:
                        f.write(img_response.content)
                    downloaded_images.append(image_path)
                except requests.RequestException as e:
                    print(f"Error downloading image: {e}")

            start_index += 10
        except requests.RequestException as e:
            print(f"Error in API request: {e}")
            break

    return downloaded_images

def compress_images_to_zip(image_paths, zip_name='images.zip'):
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for image_path in image_paths:
            zipf.write(image_path, os.path.basename(image_path))
    return zip_name

def send_email_with_attachment(receiver_email, subject, body, attachment_path, sender_email, sender_password):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with open(attachment_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())

    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
    msg.attach(part)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
        st.success("Email sent successfully!")
    except smtplib.SMTPAuthenticationError:
        st.error("Failed to authenticate. Please check your email and App Password.")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

st.title("Google Image Downloader & Emailer")
st.write("Download images from Google and send them via email.")

receiver_email = st.text_input("Enter the receiver's email address:")
query = st.text_input("Enter the search query for images:")
num_images = st.number_input("Enter the number of images to download (max 100):", min_value=1, max_value=100, value=5)

sender_email = 'shreeya.kesarwani65@gmail.com'
sender_password = 'mkeq kdey ockq njrx'
API_KEY = 'AIzaSyB0q7Yp7z-IVBXq49Yer8DqjxGmm-MpKqE' 
CX = '200a8ead8a11e4a3b'

if st.button('Download and Send Images'):
    if not all([API_KEY, CX, sender_email, sender_password]):
        st.error("Error: Missing API credentials.")
    else:
        
        downloaded_images = search_and_download_images(query, num_images, API_KEY, CX)

        if len(downloaded_images) < num_images:
            st.warning(f"Only {len(downloaded_images)} images were downloaded.")

        
        zip_file = compress_images_to_zip(downloaded_images)

        
        send_email_with_attachment(
            receiver_email=receiver_email,
            subject=f'Your requested images for "{query}"',
            body=f'Here are the {len(downloaded_images)} images you requested for the search query: "{query}"',
            attachment_path=zip_file,
            sender_email=sender_email,
            sender_password=sender_password
        )

        
        os.remove(zip_file)
        for file in downloaded_images:
            os.remove(file)
        shutil.rmtree(os.path.dirname(downloaded_images[0]))
