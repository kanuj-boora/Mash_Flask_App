import os, shutil
import zipfile
from flask import Flask, request, redirect, render_template, flash
from flask_mail import Mail, Message
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import concatenate_audioclips
from pytube import YouTube, Search


MEDIA_PATH = os.path.join(os.getcwd(), '/media/')

app = Flask(__name__)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'kanujboora0110@gmail.com'
app.config['MAIL_PASSWORD'] = 'ctufybsodzxhtnqd'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        singer = request.form["singer"]
        n = int(request.form["n"])
        y = int(request.form["y"])
        recv_email = str(request.form["email"])

        audios = download_audio(singer, n)
        cut_audios = cut_audio(audios, y)
        merge_audios(cut_audios)
        zip_file = create_zip()
        send_email(recv_email, zip_file)
        
        remove_files(MEDIA_PATH)
        # flash('Email Sent')

        return redirect("/")

    return render_template("index.html")

def download_single_video(video, singer, i):
    try:
        yt = YouTube(video.watch_url)
        if yt.length <= 420 and singer in yt.title.lower():
            print(f"Downloading video: {yt.title}")
            video = yt.streams.filter(only_audio=True).first()
            video.download(MEDIA_PATH, filename=f"audio{i}.mp4")
            return True
        else:
            print(f"Video longer than 6 minutes: {yt.title}")
            return False
    except:
        print(f"Failed to download video: {video}")
        return False

def download_audio(singer, n):
    query = singer + ' songs'
    video_list = Search(query.lower())
    
    while(len(video_list.results) < 5*n):
        video_list.get_next_results()
    
    audios = []
    count = 1

    if not os.path.isdir('media'):
        os.mkdir(os.getcwd()+'/media')
    
    for video in video_list.results:
        if count == n+1:
            print('Required number downloaded')
            break
        if download_single_video(video, singer, count):
            audios.append(MEDIA_PATH+f"audio{count}.mp4")
            count += 1
 
    return audios

def cut_audio(audios, y):
    cut_audios = []
    for i, audio in enumerate(audios):
        clip = AudioFileClip(audio)
        cut_clip = clip.subclip(0, y)
        cut_clip.write_audiofile(MEDIA_PATH+f"cut_audio{i}.mp3")
        cut_audios.append(MEDIA_PATH+f"cut_audio{i}.mp3")
        clip.close()
        
    return cut_audios

def merge_audios(cut_audios):
    cut_audio_file = [AudioFileClip(c) for c in cut_audios]
    output_audio = concatenate_audioclips(cut_audio_file)
    output_audio.write_audiofile(MEDIA_PATH+'output_audio.mp3')

def create_zip():
    zip_file = './media/output.zip'
    with zipfile.ZipFile(zip_file, 'w') as f:
        f.write('./media/output_audio.mp3')
    return zip_file

def send_email(recv_email, zip_file):
    try:
        msg = Message('Output audio file is in attachment',
                            sender = 'kanujboora0110@gmail.com',
                            recipients = [recv_email]
                            )
        msg.body = "Output audio file is in attachment"
        with app.open_resource(zip_file) as f:
            msg.attach('./media/output.zip', 'application/zip', f.read())
        mail.send(msg)
        flash('Email sent')
    except Exception as e:
        print(f"Error in sending Email: {e}")
        
def remove_files(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


if __name__ == "__main__":
    app.run()
