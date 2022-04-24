from fpdf import FPDF
from multiprocessing import Pool
from pathlib import Path
import json
import pika
import time

def SaveStatPdf(username, dir):
    userFolder = f'{dir}/{username}'

    statFilePath = f'{userFolder}/stat.json'
    infoFilePath = f'{userFolder}/info.json'
    imagePath = f'{userFolder}/img.jpeg'

    pdf = FPDF()

    pdf.add_page()
    pdf.set_font("Arial", size=12)

    infoFile = Path(infoFilePath)
    info = json.loads(infoFile.read_text())

    pdf.cell(105)
    pdf.cell(0, 5, f'{info["name"]}, {info["sex"]}', ln=1)
    pdf.cell(105)
    pdf.cell(0, 5, f'{info["email"]}', ln=1)

    statFile = Path(statFilePath)
    stat = json.loads(statFile.read_text())

    pdf.ln(2)
    pdf.cell(105)
    pdf.cell(0, 5, f'Play time: {stat["play_time"]}', ln=1)
    pdf.cell(105)
    pdf.cell(0, 5, f'Sessions: {stat["sessions"]}', ln=1)
    pdf.cell(105)
    pdf.cell(0, 5, f'Wins: {stat["wins"]}', ln=1)
    pdf.cell(105)
    pdf.cell(0, 5, f'Losses: {stat["losses"]}', ln=1)

    pdf.image(imagePath, x=10, y=10, w=100)

    pdf.output(f'{userFolder}/{username}.pdf')

def callback(ch, method, properties, body):
    username, dir = body.decode().split()
    print(f" [x] Received request for {username}", flush = True)
    SaveStatPdf(username, dir)
    print(f" [x] Done {username}.pdf", flush = True)
    ch.basic_ack(delivery_tag = method.delivery_tag)

while True:
    try:
        # connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost')) # for local tests
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq')) # for docker compose
        channel = connection.channel()
        channel.queue_declare(queue='task_queue', durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='task_queue', on_message_callback=callback)
        print(' [*] Waiting for messages. To exit press CTRL+C', flush = True)
        channel.start_consuming()
    except Exception as e:
        print(f'Error: {e}', flush = True)
        time.sleep(1)
