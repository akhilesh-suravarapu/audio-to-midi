# necessary
from flask import Flask, render_template, request, send_file, flash, redirect # everything on the web
from flask_sqlalchemy import SQLAlchemy # SQL table
from yt_dlp import YoutubeDL # to convert from youtube to mp3
import midifier  # MIDI conversion module
# useful
import tempfile # downloads youtube video to a file
from io import BytesIO # so it's not all loaded in memory
import os # delete the tempfile and set secret
import datetime # records date created
from threading import Thread # to run in the background


# Initialize Flask and SQLite
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get("SECRET_KEY", "AQA7517ComputerScienceNEA")
# IN RELEASE:
# env SECRET_KEY
# import secrets
# secrets.token_hex(16)

db = SQLAlchemy(app)


# Database table
class Upload(db.Model):
    __tablename__ = 'ytupload'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    artist = db.Column(db.String)
    date_added = db.Column(db.Date)
    length = db.Column(db.Integer)
    bpm = db.Column(db.Integer)
    key = db.Column(db.String(3))
    instrument = db.Column(db.String(6))
    confidence = db.Column(db.Integer)
    url = db.Column(db.String(11))
    data = db.Column(db.LargeBinary)




# --- FUNCTIONS ---

# get youtube metadata without downloading
def metadata(url):
    ydl_opts = {'quiet': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


# download youtube audio as mp3 and return path
def youtube_to_mp3(url):
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_path = temp_file.name
    temp_file.close()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_path + '.%(ext)s',  # safe temporary path
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return temp_path + '.mp3'

# convert in the background
def background_convert(url, instrument, confidence):
    with app.app_context():
        path = youtube_to_mp3(url)
        midi = midifier.find_notes(path, instrument, confidence)

        info = metadata(url)
        title = info.get("title", "Unknown")
        artist, title = clean_title(title)
        if not artist:
            artist = info.get("uploader", "Unknown")

        upload = Upload(
            title=title,
            artist=artist,
            date_added=datetime.date.today(),
            length=midi[0],
            bpm=102,
            key=midi[1],
            instrument=instrument,
            confidence=confidence,
            url=url,
            data=midi[2].getvalue()
        )
        db.session.add(upload)
        db.session.commit()
        os.remove(path)

# to sort out youtube titles
def clean_title(title):
    # split on the first matching separator
    separators = [' - ', ' – ', ' — ']
    parts = next((title.split(sep, 1) for sep in separators if sep in title), [title])

    if len(parts) >= 2: # sometimes there can be multiple, parts[2+] is ignored
        artist = parts[0]
        song_title = parts[1] # seems to be the standard
    else:
        artist = None
        song_title = parts[0]

    # often contains random info after '[', '|', '(', ':'
    for char in ['[', '|', '(', ':']:
        if char in song_title:
            song_title = song_title.split(char, 1)[0]
            break

    return artist, song_title # can't access publisher, I'll sort later



# --- APP ROUTES ---
@app.route('/', methods=['GET', 'POST']) # POST is for files, GET is for urls
def index():
    if request.method == 'POST':
        # file upload
        file = request.files.get('file')
        instrument = request.form.get('instrument', 'piano')
        confidence = int(request.form.get('conf', 90))/100

        if not file:
            flash("No file uploaded.")
            return redirect('/')

        allowed = ['.wav','.mp3', '.aac', '.flac', '.ogg']
        if not any(file.filename.lower().endswith(x) for x in allowed):
            flash("Only .wav, .mp3, .aac, .flac, .ogg files are allowed.")
            return redirect('/')

        midi = midifier.find_notes(file, instrument, confidence)
        return send_file(
            midi[2],
            as_attachment=True,
            mimetype="audio/midi",
            download_name=file.filename
        )

    url = request.args.get("url")
    if not url:
        return render_template("index.html") # not POST or GET - render front page

    # GET
    url = url[-11:] # formatting

    try:
        metadata(url)
    except:
        flash("URL does not lead to a valid YouTube video.")
        return redirect('/')

    instrument = request.form.get('instrument', 'piano')
    confidence = int(request.form.get('conf', 90))/100
    
    # check if this URL has been transcribed
    existing = db.session.execute(
        db.text(
            "SELECT * FROM ytupload "
            "WHERE url = :link"
        ),
        {"link": url}
    ).mappings().all()
    if existing:
        return render_template("confirm_download.html", uploads=existing, video_id = url)  # pass the query result
    
    return redirect(f"/convert/{url}?inst={instrument}&conf={confidence}")

# let user know their request went through
@app.route('/convert/<url>')
def convert(url):
    instrument = request.args.get("inst", "piano")
    confidence = float(request.args.get("conf", 0.9))

    Thread(target=background_convert, args=(url, instrument, confidence)).start()

    return render_template("convert.html", url=url)

# download saved MIDI from database
@app.route('/download/<int:upload_id>')
def download(upload_id):
    upload = Upload.query.get_or_404(upload_id)
    return send_file(
        BytesIO(upload.data),
        as_attachment=True,
        mimetype="audio/midi",
        download_name=f"{upload.title} - {upload.artist}.mid"
    )


# display database table
@app.route('/database')
def show_all():
    search = request.args.get('v', '')
    result = db.session.execute(
        db.text(
            "SELECT * FROM ytupload "
            "WHERE UPPER(artist) LIKE UPPER(:search) "
            "OR UPPER(title) LIKE UPPER(:search)"
        ),
        {"search": f"%{search}%"}
    ).mappings().all()
    return render_template("database.html", uploads=result)

# about
@app.route('/about')
def about():
    return render_template("about.html")


# finally, run the code
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
