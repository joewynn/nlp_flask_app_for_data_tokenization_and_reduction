from flask import Flask, url_for, render_template, redirect, request
from flask_uploads import UploadSet, configure_uploads, ALL, DATA
from werkzeug.utils import secure_filename
from uuid import uuid4

# Other packages
import os
import time

time_string = time.strftime("%Y%m%d-%H%M%S")

# NLP
import spacy
nlp = spacy.load('en_core_web_sm')

entity_selection = {
    "names": "PERSON",
    "birthday": "DATE",
    "credit_card": "CREDIT_CARD",
    "phone_number": "PHONE_NUMBER",
    "email": "EMAIL",
    "place": "GPE",
    "organization": 'ORG'
}


# Functions to Tokenize and Identify Text
def sanitize_text(text, choice):
    docx = nlp(text)
    redacted_sentences = []
    #print("The Key is: {} ".format(entity_selection[choice]))
    for ent in docx.ents:
        print(ent.merge())
    for token in docx:
        if token.ent_type_ == entity_selection[choice]:
            redacted_sentences.append(" [REDACTED {} ] ".format(entity_selection[choice]))
        else:
            redacted_sentences.append(token.string)
    return "".join(redacted_sentences)


def tokenize_text(text, choice):
    docx = nlp(text)
    tokenized_sentences = []
    #print("The Key is: {} ".format(entity_selection[choice]))
    for ent in docx.ents:
        print(ent.merge())
    for token in docx:
        if token.ent_type_ == entity_selection[choice]:
            token_id = str(uuid4()).split('-')[0]
            tokenized_sentences.append(" {}_{} ".format(entity_selection[choice], token_id))
        else:
            tokenized_sentences.append(token.string)
    return "".join(tokenized_sentences)



def write_to_file(text):
    file_name = 'nlp_text' + time_string + '.txt'
    with open(os.path.join('static/download', file_name), 'w') as f:
        f.write(text)

app = Flask(__name__)

# Configurations
files = UploadSet('files', ALL)
app.config['UPLOADED_FILES_DEST'] = 'static/upload'
configure_uploads(app, files)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/uploads', methods=['GET', 'POST'])
def uploads():
    if request.method == 'POST' and 'txt_data' in request.files:
        file = request.files['txt_data']
        save_choice = request.form['save_option']
        filename = secure_filename(file.filename)
        file.save(os.path.join('static/upload', filename))

        # Document sanitization
        with open(os.path.join('static/upload', filename), 'r+') as f:
            file_text = f.read()
            results = sanitize_text(file_text, 'birthday')

        if save_choice == 'save_to_text':
            new_result = write_to_file(results)
            return redirect(url_for('download'))
        elif save_choice == 'no_save':
            pass
        else:
            pass

    return render_template("results.html", file_text=file_text, results=results)


@app.route('/sanitize', methods=['GET', 'POST'])
def sanitize():
    """
    Reducting a type of context information based on the user's choice.
    The user input/choice could be either:
    @:param     rawtext         Raw text from the user
    @:param     birthday        user date of birth appearing on the text
    @:param     names           user names which could full names or first names or last names
    @:param     credit_card     credit card(s)
    @:param     phone_number    phone numbers
    @:param     email           email address
    return :
        a html rendering with original text (rawtext) and output text with reducted text side by side
     """
    if request.method == 'POST':
        rawtext = request.form['rawtext']
        choice = request.form['use_case_option']
        print("I want to Sanitize {}".format(choice))
        results = sanitize_text(rawtext, choice)
    return render_template("index.html", results=results, rawtext=rawtext)


@app.route('/tokenize', methods=['GET', 'POST'])
def tokenize():
    if request.method == 'POST':
        rawtext = request.form['rawtext']
        choice = request.form['use_case_option']
        print("I want to Tokenize {}".format(choice))
        results = tokenize_text(rawtext, choice)
    return render_template("index.html", results=results, rawtext=rawtext)


@app.route('/downloads', methods=['GET', 'POST'])
def download():
    files_list = os.listdir(os.path.join('static/download'))
    return render_template("downloads_list.html", files=files_list)


if __name__ == '__main__':
    app.run(debug=True)
