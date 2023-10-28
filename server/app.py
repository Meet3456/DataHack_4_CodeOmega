from flask import Flask, jsonify, request, session, url_for, redirect
from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)
passw = os.getenv("MONGO_PASS")
app.secret_key = os.getenv("SECRET_KEY")


def auth_middleware():
    if 'user_id' not in session:
        return redirect(url_for('login'))


connection_string = f"mongodb+srv://codeomega:{passw}@cluster0.hnyk6mi.mongodb.net/?retryWrites=true&w=majority"


def MongoDB(collection_name):
    client = MongoClient(connection_string)
    db = client.get_database('datahack')
    collection = db.get_collection(collection_name)
    return collection


@app.route('/register-post', methods=['POST'])
def registerpost():
    data = request.get_json()
    new_record = {
        'username': data.get('username'),
        'email': data.get('email'),
        'password': data.get('password'),
    }
    collection = MongoDB('users')
    existing_user = collection.find_one({'email': new_record['email']})
    if existing_user:
        response = {'message': 'exists'}
        return jsonify(response)

    result = collection.insert_one(new_record)
    if result.inserted_id:
        return jsonify({'message': True})
    else:
        response = {'message': False}
        return jsonify(response)


@app.route('/login', methods=['POST'])
def loginpost():
    record = {
        'password': request.form.get('logpass'),
        'email': request.form.get('logemail'),
        'type': request.form.get('type'),
    }
    collection_name = 'applicant' if record['type'] == 'applicant' else 'recruiter'
    collection = MongoDB(collection_name)
    existing_user = collection.find_one({'email': record['email']})
    if existing_user:
        if existing_user['password'] == record['password']:
            response = {'success': True}
            session['user_id'] = str(existing_user['_id'])
            print(session['user_id'])
            return jsonify(response)
        else:
            response = {'success': 'password_mismatch'}
            return jsonify(response)
    else:
        response = {'success': False}
        return jsonify(response)



def vedant_raita(in_pdf,out_pdf):
    #========================DO NOT CHANGE==========================
    import PyPDF2
    from reportlab.pdfgen import canvas
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    from PyPDF2 import PdfReader

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph
    from fpdf import FPDF
    import textwrap

    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, PageTemplate, BaseDocTemplate, Frame, PageBreak, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from langdetect import detect

    def extract_text_from_pdf(file_path):
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        code=detect(text)
        print(code)

        # d={'fr':'fra_Latn',}


        return text,code

    def translate_text(text, source_lang, target_lang= 'eng_Latn'):
        tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M", src_lang = source_lang)
        model = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M")
        inputs = tokenizer(text, return_tensors="pt")
        translated_tokens = model.generate(
            inputs['input_ids'], forced_bos_token_id=tokenizer.lang_code_to_id[target_lang], max_length=1024
        )
        result = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
        print(result)
        return result

    def translate_pdf_to_english(file_path):
        text,code = extract_text_from_pdf(file_path)
        # Split the text into chunks of approximately 1000 characters
        chunks = textwrap.wrap(text, width=1000)
        translated_text = ""
        for chunk in chunks:
            translated_text += translate_text(chunk,code)
        return translated_text

    def create_pdf(text, output_path):
        pdf_filename = "output.pdf"

        class MyDocTemplate(BaseDocTemplate):
            def afterFlowable(self, flowable):
                if isinstance(flowable, Paragraph):
                    if flowable.getKeepWithNext():
                        self.canv.restoreState()
                        self.canv.showPage()
                        self.handle_flowable(flowable)

        doc = MyDocTemplate(pdf_filename, pagesize=letter)

        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        template = PageTemplate(id='test', frames=frame)
        doc.addPageTemplates([template])

        # Create a list of flowables (content elements)
        story = []
        styles = getSampleStyleSheet()
        paragraphs = text.split('\n\n')

        # Customize the font size
        custom_style = styles["Normal"]
        custom_style.fontName = 'Helvetica'
        custom_style.fontSize = 12 # Set the font size here
        custom_style.alignment = 0 

        for paragraph in paragraphs:
            story.append(Paragraph(paragraph, custom_style))
            story.append(PageBreak())

        # Remove the page break after the last paragraph
        story.pop()

        # Build the PDF
        doc.build(story)
        print(f"PDF saved as {pdf_filename}")


    translated_text = translate_pdf_to_english(in_pdf)
    create_pdf(translated_text, out_pdf)
    #++++++++++++++++++++++++++++DO NOT CHANGE+++++++++++++++++++++++++++++






if __name__ == "__main__":
    app.run(debug=True, port=5000)
