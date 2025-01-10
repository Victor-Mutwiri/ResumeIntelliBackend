from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
from werkzeug.utils import secure_filename
from app.services.resume_analyzer import ResumeAnalyzer
from app.utils.pdf_utils import read_text_from_pdf
import os
from dotenv import load_dotenv

load_dotenv()

# Add multiple origins for development
allowed_origins = ["https://resume-intelli.vercel.app"]

if os.getenv('FLASK_ENV') == 'development':
    allowed_origins.extend(["http://localhost:3000", "http://127.0.0.1:5000", "http://localhost:5173"])

api = Blueprint('api', __name__)
CORS(api, origins=allowed_origins)

analyzer = None

def init_analyzer():
    global analyzer
    if analyzer is None:
        analyzer = ResumeAnalyzer(os.getenv('GROQ_API_KEY'))

@api.before_request
def before_request():
    init_analyzer()

# Add root endpoint
@api.route('/', methods=['GET'])
def root():
    return jsonify({
        'status': 'online',
        'message': 'Resume Analyzer API is running',
        'endpoints': {
            'analyze': '/api/analyze',
            'health': '/api/health'
        }
    })

# Add health check endpoint
@api.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Resume analyzer API is running'
    })

@api.route('/favicon.ico')
def favicon():
    return '', 204

@api.route('/api/analyze', methods=['POST'])
def analyze_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        resume_file = request.files['resume']
        
        if not hasattr(resume_file, 'filename'):
            return jsonify({'error': 'Invalid file object'}), 400
        
        job_description = request.form.get('jobDescription')
        
        if not job_description:
            return jsonify({'error': 'No job description provided'}), 400
        
        if resume_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if not resume_file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        filename = secure_filename(resume_file.filename)
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        resume_file.save(temp_path)
        
        try:
            resume_text = read_text_from_pdf(temp_path)
        finally:
            os.remove(temp_path)
        
        if not resume_text:
            return jsonify({'error': 'Could not extract text from PDF'}), 400
            
        feedback = analyzer.analyze_match_with_groq(resume_text, job_description)
        
        return jsonify({
            'feedback': feedback,
            'filename': resume_file.filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/generate_custom_resume', methods=['POST'])
def generate_custom_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        resume_file = request.files['resume']
        
        if not hasattr(resume_file, 'filename'):
            return jsonify({'error': 'Invalid file object'}), 400
        
        job_description = request.form.get('jobDescription')
        
        if not job_description:
            return jsonify({'error': 'No job description provided'}), 400
        
        if resume_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if not resume_file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        filename = secure_filename(resume_file.filename)
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        resume_file.save(temp_path)
        
        try:
            resume_text = read_text_from_pdf(temp_path)
        finally:
            os.remove(temp_path)
        
        if not resume_text:
            return jsonify({'error': 'Could not extract text from PDF'}), 400
        
        custom_resume = analyzer.generate_custom_resume_logic(resume_text, job_description)
        
        return jsonify({
            'custom_resume': custom_resume,
            'filename': resume_file.filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/generate_cover_letter', methods=['POST'])
def generate_cover_letter():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        resume_file = request.files['resume']
        
        if not hasattr(resume_file, 'filename'):
            return jsonify({'error': 'Invalid file object'}), 400
        
        job_description = request.form.get('jobDescription')
        
        if not job_description:
            return jsonify({'error': 'No job description provided'}), 400
        
        if resume_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if not resume_file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        filename = secure_filename(resume_file.filename)
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        resume_file.save(temp_path)
        
        try:
            resume_text = read_text_from_pdf(temp_path)
        finally:
            os.remove(temp_path)
        
        if not resume_text:
            return jsonify({'error': 'Could not extract text from PDF'}), 400
        
        cover_letter = analyzer.generate_cover_letter(resume_text, job_description)
        
        return jsonify({
            'cover_letter': cover_letter,
            'filename': resume_file.filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500