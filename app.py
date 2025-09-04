#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import json
import os
from functools import wraps

app = Flask(__name__, static_folder='static')
app.secret_key = secrets.token_hex(16)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Database setup
DATABASE = 'database/stroke_prediction.db'

def init_database():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            date_of_birth DATE,
            phone TEXT,
            emergency_contact TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Check if emergency_contact column exists, add it if it doesn't
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'emergency_contact' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN emergency_contact TEXT')
    
    # Admin users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create default admin user if none exists
    cursor.execute('SELECT COUNT(*) FROM admin_users')
    admin_count = cursor.fetchone()[0]
    if admin_count == 0:
        default_admin_password = hash_password('admin123')
        cursor.execute('''
            INSERT INTO admin_users (username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin@strokeprediction.com', default_admin_password, 'System Administrator', 'admin'))
    
    # Patient assessments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            patient_id TEXT,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            hypertension INTEGER NOT NULL,
            heart_disease INTEGER NOT NULL,
            ever_married TEXT NOT NULL,
            work_type TEXT NOT NULL,
            residence_type TEXT NOT NULL,
            avg_glucose_level REAL NOT NULL,
            bmi REAL NOT NULL,
            smoking_status TEXT NOT NULL,
            risk_score REAL NOT NULL,
            risk_level TEXT NOT NULL,
            risk_factors TEXT,
            recommendations TEXT,
            assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # System announcements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_active INTEGER DEFAULT 1,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES admin_users (id)
        )
    ''')
    
    # User feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            status TEXT DEFAULT 'pending',
            admin_response TEXT,
            responded_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responded_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (responded_by) REFERENCES admin_users (id)
        )
    ''')
    
    # Assessment templates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessment_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            template_data TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES admin_users (id)
        )
    ''')
    
    # Add user status and role columns if they don't exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'is_active' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1')
    if 'role' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "user"')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    """Decorator to require login for certain routes with activation check"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Check if user is still active
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT is_active FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not user[0]:  # User not found or not active
            session.clear()  # Clear session
            return redirect(url_for('deactivated_account'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/deactivated')
def deactivated_account():
    """Page for deactivated users"""
    return render_template('deactivated_account.html')

@app.route('/submit_reactivation_request', methods=['POST'])
def submit_reactivation_request():
    """Submit reactivation request for deactivated users"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Insert reactivation request as feedback
        cursor.execute('''
            INSERT INTO user_feedback (user_id, subject, message, category)
            VALUES (?, ?, ?, ?)
        ''', (data['user_id'], 'Account Reactivation Request', data['message'], 'reactivation'))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Reactivation request submitted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def admin_required(f):
    """Decorator to require admin login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

class StrokeRiskCalculator:
    """Enhanced stroke risk calculation engine with better score distribution"""
    
    def __init__(self):
        # Enhanced risk factors with graduated scoring for better distribution
        self.risk_factors = {
            'age': {
                'weight': 0.20,
                'scoring': 'graduated',
                'ranges': [
                    (0, 40, 0.0),      # Very low risk
                    (40, 50, 0.1),     # Low risk
                    (50, 60, 0.3),     # Moderate risk
                    (60, 70, 0.6),     # High risk
                    (70, 80, 0.8),     # Very high risk
                    (80, 120, 1.0)     # Maximum risk
                ]
            },
            'hypertension': {'weight': 0.18, 'scoring': 'binary'},
            'heart_disease': {'weight': 0.16, 'scoring': 'binary'},
            'avg_glucose_level': {
                'weight': 0.14,
                'scoring': 'graduated',
                'ranges': [
                    (0, 100, 0.0),     # Normal
                    (100, 126, 0.3),   # Pre-diabetic
                    (126, 180, 0.6),   # Diabetic
                    (180, 250, 0.8),   # Poorly controlled
                    (250, 500, 1.0)    # Severe
                ]
            },
            'bmi': {
                'weight': 0.12,
                'scoring': 'graduated',
                'ranges': [
                    (0, 18.5, 0.1),    # Underweight (slight risk)
                    (18.5, 25, 0.0),   # Normal
                    (25, 30, 0.3),     # Overweight
                    (30, 35, 0.6),     # Obese Class I
                    (35, 40, 0.8),     # Obese Class II
                    (40, 60, 1.0)      # Obese Class III
                ]
            },
            'smoking_status': {
                'weight': 0.12,
                'scoring': 'categorical',
                'values': {
                    'never smoked': 0.0,
                    'formerly smoked': 0.4,
                    'smokes': 1.0,
                    'Unknown': 0.2
                }
            },
            'work_type': {
                'weight': 0.04,
                'scoring': 'categorical',
                'values': {
                    'children': 0.0,
                    'Govt_job': 0.2,
                    'Never_worked': 0.1,
                    'Private': 0.6,
                    'Self-employed': 0.8
                }
            },
            'residence_type': {
                'weight': 0.02,
                'scoring': 'categorical',
                'values': {
                    'Rural': 0.0,
                    'Urban': 0.5
                }
            },
            'gender': {
                'weight': 0.02,
                'scoring': 'categorical',
                'values': {
                    'Female': 0.0,
                    'Male': 0.6,
                    'Other': 0.3
                }
            }
        }
        
        # More nuanced risk level thresholds for better distribution
        self.risk_thresholds = {
            'Very Low': 0.15,
            'Low': 0.30,
            'Moderate': 0.50,
            'High': 0.70,
            'Very High': 0.85,
            'Critical': 1.0
        }
    
    def calculate_risk_score(self, patient_data):
        """Calculate numerical risk score with graduated scoring for better distribution"""
        total_score = 0.0
        
        for factor_name, factor_config in self.risk_factors.items():
            if factor_name not in patient_data:
                continue
                
            factor_value = patient_data[factor_name]
            factor_weight = factor_config['weight']
            scoring_type = factor_config['scoring']
            
            if scoring_type == 'graduated':
                # Use graduated scoring based on ranges
                ranges = factor_config['ranges']
                factor_score = 0.0
                
                for min_val, max_val, score_multiplier in ranges:
                    if min_val <= factor_value < max_val:
                        # Linear interpolation within range for smoother distribution
                        if max_val > min_val:
                            range_position = (factor_value - min_val) / (max_val - min_val)
                            factor_score = score_multiplier * (0.5 + 0.5 * range_position)
                        else:
                            factor_score = score_multiplier
                        break
                
                total_score += factor_weight * factor_score
                
            elif scoring_type == 'binary':
                # Binary scoring (0 or 1)
                if factor_value == 1:
                    total_score += factor_weight
                    
            elif scoring_type == 'categorical':
                # Categorical scoring with specific values
                values_map = factor_config['values']
                if factor_value in values_map:
                    total_score += factor_weight * values_map[factor_value]
        
        # Add some randomization for better distribution (±2% variation)
        import random
        variation = random.uniform(-0.02, 0.02)
        total_score = max(0.0, min(1.0, total_score + variation))
        
        return total_score
    
    def identify_risk_factors(self, patient_data):
        """Identify present risk factors with graduated assessment"""
        factors = []
        
        # Age assessment with graduated levels
        age = patient_data.get('age', 0)
        if age >= 80:
            factors.append("Very advanced age (≥80 years) - Critical Risk")
        elif age >= 70:
            factors.append("Advanced age (70-79 years) - High Risk")
        elif age >= 60:
            factors.append("Mature age (60-69 years) - Moderate Risk")
        elif age >= 50:
            factors.append("Middle age (50-59 years) - Low Risk")
        
        # Binary risk factors
        if patient_data.get('hypertension') == 1:
            factors.append("Hypertension - High Risk")
        if patient_data.get('heart_disease') == 1:
            factors.append("Heart disease - High Risk")
        
        # Glucose level assessment
        glucose = patient_data.get('avg_glucose_level', 0)
        if glucose >= 250:
            factors.append("Severely elevated glucose (≥250 mg/dL) - Critical Risk")
        elif glucose >= 180:
            factors.append("Poorly controlled diabetes (180-249 mg/dL) - High Risk")
        elif glucose >= 126:
            factors.append("Diabetes (126-179 mg/dL) - Moderate Risk")
        elif glucose >= 100:
            factors.append("Pre-diabetes (100-125 mg/dL) - Low Risk")
        
        # BMI assessment
        bmi = patient_data.get('bmi', 0)
        if bmi >= 40:
            factors.append("Severe obesity (BMI ≥40) - Critical Risk")
        elif bmi >= 35:
            factors.append("Moderate obesity (BMI 35-39.9) - High Risk")
        elif bmi >= 30:
            factors.append("Obesity (BMI 30-34.9) - Moderate Risk")
        elif bmi >= 25:
            factors.append("Overweight (BMI 25-29.9) - Low Risk")
        elif bmi < 18.5:
            factors.append("Underweight (BMI <18.5) - Low Risk")
        
        # Smoking status
        smoking = patient_data.get('smoking_status', '')
        if smoking == 'smokes':
            factors.append("Current smoker - Critical Risk")
        elif smoking == 'formerly smoked':
            factors.append("Former smoker - Moderate Risk")
        elif smoking == 'Unknown':
            factors.append("Unknown smoking status - Low Risk")
        
        # Work type
        work = patient_data.get('work_type', '')
        if work == 'Self-employed':
            factors.append("Self-employed work - Moderate Risk")
        elif work == 'Private':
            factors.append("Private sector work - Low Risk")
        
        # Other factors
        if patient_data.get('gender') == 'Male':
            factors.append("Male gender - Low Risk")
        if patient_data.get('residence_type') == 'Urban':
            factors.append("Urban residence - Low Risk")
            
        return factors
    
    def generate_recommendations(self, risk_level, patient_data):
        """Generate personalized recommendations based on enhanced risk assessment"""
        recommendations = []
        
        # Base recommendations for all risk levels
        if risk_level == "Very Low":
            recommendations.extend([
                "Maintain current healthy lifestyle",
                "Annual health check-ups recommended",
                "Continue regular physical activity",
                "Maintain balanced diet"
            ])
        elif risk_level == "Low":
            recommendations.extend([
                "Continue preventive care measures",
                "Monitor blood pressure quarterly",
                "Maintain healthy diet and exercise routine",
                "Consider lifestyle optimization"
            ])
        elif risk_level == "Moderate":
            recommendations.extend([
                "Schedule medical consultation within 2-4 weeks",
                "Monitor blood pressure monthly",
                "Implement structured exercise program",
                "Consider dietary consultation"
            ])
        elif risk_level == "High":
            recommendations.extend([
                "🚨 Schedule medical consultation within 1 week",
                "Monitor blood pressure weekly",
                "Implement immediate lifestyle changes",
                "Consider cardiovascular screening"
            ])
        elif risk_level == "Very High":
            recommendations.extend([
                "🚨 URGENT: Schedule medical consultation within 2-3 days",
                "Daily blood pressure monitoring",
                "Immediate lifestyle intervention required",
                "Comprehensive cardiovascular assessment needed"
            ])
        elif risk_level == "Critical":
            recommendations.extend([
                "🚨 CRITICAL: Seek immediate medical attention (within 24 hours)",
                "Continuous health monitoring required",
                "Emergency action plan needed",
                "Immediate specialist referral recommended"
            ])
        
        # Specific recommendations based on risk factors
        if patient_data.get('hypertension') == 1:
            recommendations.append("Follow prescribed hypertension medication regimen strictly")
        
        if patient_data.get('heart_disease') == 1:
            recommendations.append("Cardiology follow-up and medication compliance essential")
        
        glucose = patient_data.get('avg_glucose_level', 0)
        if glucose >= 250:
            recommendations.append("🚨 URGENT: Immediate diabetes management required")
        elif glucose >= 126:
            recommendations.append("Diabetes management and glucose monitoring essential")
        elif glucose >= 100:
            recommendations.append("Pre-diabetes management - lifestyle changes recommended")
        
        bmi = patient_data.get('bmi', 0)
        if bmi >= 35:
            recommendations.append("🚨 Urgent weight management - consider bariatric consultation")
        elif bmi >= 30:
            recommendations.append("Weight management program recommended")
        elif bmi >= 25:
            recommendations.append("Gradual weight reduction through diet and exercise")
        
        if patient_data.get('smoking_status') == 'smokes':
            recommendations.append("🚨 CRITICAL: Immediate smoking cessation required - seek professional help")
        elif patient_data.get('smoking_status') == 'formerly smoked':
            recommendations.append("Continue smoke-free lifestyle - avoid relapse triggers")
        
        # Age-specific recommendations
        age = patient_data.get('age', 0)
        if age >= 70:
            recommendations.append("Regular geriatric health assessments recommended")
        elif age >= 60:
            recommendations.append("Enhanced preventive care for mature adults")
        
        # Always include stroke awareness
        if risk_level in ["High", "Very High", "Critical"]:
            recommendations.append("🧠 Learn F.A.S.T. stroke warning signs: Face, Arms, Speech, Time")
        
        return recommendations
    
    def predict_stroke_risk(self, patient_data):
        """Main prediction function with enhanced distribution"""
        # Calculate risk score with graduated system
        risk_score = self.calculate_risk_score(patient_data)
        
        # Determine risk level using enhanced thresholds
        risk_level = "Critical"  # Default to highest risk
        for level, threshold in sorted(self.risk_thresholds.items(), key=lambda x: x[1]):
            if risk_score <= threshold:
                risk_level = level
                break
        
        # Get detailed risk factors and recommendations
        risk_factors = self.identify_risk_factors(patient_data)
        recommendations = self.generate_recommendations(risk_level, patient_data)
        
        # Calculate confidence score based on data completeness
        total_factors = len(self.risk_factors)
        provided_factors = sum(1 for key in self.risk_factors.keys() if key in patient_data and patient_data[key] is not None)
        confidence = (provided_factors / total_factors) * 100
        
        return {
            'risk_score': round(risk_score, 4),  # More precision for better distribution
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'confidence': round(confidence, 1),
            'score_breakdown': self._get_score_breakdown(patient_data)
        }
    
    def _get_score_breakdown(self, patient_data):
        """Get detailed breakdown of risk score components for visualization"""
        breakdown = {}
        
        for factor_name, factor_config in self.risk_factors.items():
            if factor_name not in patient_data:
                breakdown[factor_name] = {'contribution': 0.0, 'weight': factor_config['weight']}
                continue
                
            factor_value = patient_data[factor_name]
            factor_weight = factor_config['weight']
            scoring_type = factor_config['scoring']
            
            if scoring_type == 'graduated':
                ranges = factor_config['ranges']
                factor_score = 0.0
                
                for min_val, max_val, score_multiplier in ranges:
                    if min_val <= factor_value < max_val:
                        if max_val > min_val:
                            range_position = (factor_value - min_val) / (max_val - min_val)
                            factor_score = score_multiplier * (0.5 + 0.5 * range_position)
                        else:
                            factor_score = score_multiplier
                        break
                
                contribution = factor_weight * factor_score
                
            elif scoring_type == 'binary':
                contribution = factor_weight if factor_value == 1 else 0.0
                
            elif scoring_type == 'categorical':
                values_map = factor_config['values']
                multiplier = values_map.get(factor_value, 0.0)
                contribution = factor_weight * multiplier
            else:
                contribution = 0.0
            
            breakdown[factor_name] = {
                'contribution': round(contribution, 4),
                'weight': factor_weight,
                'value': factor_value
            }
        
        return breakdown

# Initialize risk calculator
risk_calculator = StrokeRiskCalculator()

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            full_name = data.get('full_name')
            date_of_birth = data.get('date_of_birth')
            phone = data.get('phone')
            
            if not all([username, email, password, full_name]):
                return jsonify({'success': False, 'message': 'All required fields must be filled'})
            
            # Validate date of birth (must be at least 3 months old)
            if date_of_birth:
                from datetime import datetime, timedelta
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
                three_months_ago = datetime.now() - timedelta(days=90)
                if dob > three_months_ago:
                    return jsonify({'success': False, 'message': 'Patient must be at least 3 months old'})
            
            # Check if user already exists
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Username or email already exists'})
            
            # Create new user
            password_hash = hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, date_of_birth, phone, emergency_contact)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, date_of_birth, phone, data.get('emergency_contact')))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Registration successful'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with activation status check"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'success': False, 'message': 'Username and password required'})
            
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT id, password_hash, full_name, is_active FROM users WHERE username = ? OR email = ?', 
                          (username, username))
            user = cursor.fetchone()
            
            if user and user[1] == hash_password(password):
                # Check if user is active
                if not user[3]:  # is_active is False
                    conn.close()
                    return jsonify({
                        'success': False, 
                        'message': 'Account deactivated', 
                        'deactivated': True,
                        'user_id': user[0]
                    })
                
                session['user_id'] = user[0]
                session['username'] = username
                session['full_name'] = user[2]
                session.permanent = True
                
                # Update last login
                cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                              (datetime.now(), user[0]))
                conn.commit()
                conn.close()
                
                return jsonify({'success': True, 'message': 'Login successful'})
            else:
                conn.close()
                return jsonify({'success': False, 'message': 'Invalid credentials'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Login failed: {str(e)}'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Patient dashboard"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get recent assessments
    cursor.execute('''
        SELECT id, risk_level, risk_score, assessment_date 
        FROM assessments 
        WHERE user_id = ? 
        ORDER BY assessment_date DESC 
        LIMIT 5
    ''', (session['user_id'],))
    
    recent_assessments = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html', 
                         full_name=session.get('full_name'),
                         recent_assessments=recent_assessments)

@app.route('/assessment', methods=['GET', 'POST'])
@login_required
def assessment():
    """Stroke risk assessment - optimized for speed"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Quick validation of required fields
            required_fields = ['age', 'gender', 'hypertension', 'heart_disease', 
                              'ever_married', 'work_type', 'residence_type', 
                              'avg_glucose_level', 'bmi', 'smoking_status']
            
            missing_fields = [field for field in required_fields if field not in data or data[field] == '']
            if missing_fields:
                return jsonify({'success': False, 'message': f'Missing fields: {", ".join(missing_fields)}'})
            
            # Convert numeric fields efficiently
            try:
                data['age'] = int(data['age'])
                data['hypertension'] = int(data['hypertension'])
                data['heart_disease'] = int(data['heart_disease'])
                data['avg_glucose_level'] = float(data['avg_glucose_level'])
                data['bmi'] = float(data['bmi'])
            except (ValueError, TypeError) as e:
                return jsonify({'success': False, 'message': f'Invalid numeric values: {str(e)}'})
            
            # Calculate risk - optimized calculation
            risk_result = risk_calculator.predict_stroke_risk(data)
            
            # Identify most significant risk factor
            if risk_result['risk_factors']:
                risk_result['most_significant_factor'] = risk_result['risk_factors'][0]
            
            # Generate patient ID efficiently
            patient_id = f"patient_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Save assessment to database with optimized query
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO assessments (
                    user_id, patient_id, age, gender, hypertension, heart_disease,
                    ever_married, work_type, residence_type, avg_glucose_level, bmi,
                    smoking_status, risk_score, risk_level, risk_factors, recommendations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['user_id'], patient_id, data['age'], data['gender'],
                data['hypertension'], data['heart_disease'], data['ever_married'],
                data['work_type'], data['residence_type'], data['avg_glucose_level'],
                data['bmi'], data['smoking_status'], risk_result['risk_score'],
                risk_result['risk_level'], json.dumps(risk_result['risk_factors']),
                json.dumps(risk_result['recommendations'])
            ))
            
            assessment_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'assessment_id': assessment_id,
                'result': risk_result
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Assessment failed: {str(e)}'})
    
    return render_template('assessment.html')

@app.route('/history')
@login_required
def history():
    """Assessment history"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, patient_id, age, gender, risk_level, risk_score, assessment_date
        FROM assessments 
        WHERE user_id = ? 
        ORDER BY assessment_date DESC
    ''', (session['user_id'],))
    
    assessments = cursor.fetchall()
    conn.close()
    
    return render_template('history.html', assessments=assessments)

@app.route('/assessment/<int:assessment_id>')
@login_required
def view_assessment(assessment_id):
    """View detailed assessment"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get user's full name if not in session
    if 'full_name' not in session:
        cursor.execute('SELECT full_name FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        if user:
            session['full_name'] = user[0]
    
    cursor.execute('''
        SELECT * FROM assessments 
        WHERE id = ? AND user_id = ?
    ''', (assessment_id, session['user_id']))
    
    assessment = cursor.fetchone()
    conn.close()
    
    if not assessment:
        return redirect(url_for('history'))
    
    # Parse JSON fields
    risk_factors = json.loads(assessment[15]) if assessment[15] else []
    recommendations = json.loads(assessment[16]) if assessment[16] else []
    
    return render_template('view_assessment.html', 
                         assessment=assessment,
                         risk_factors=risk_factors,
                         recommendations=recommendations)

@app.route('/find_health_facility')
@login_required
def find_health_facility():
    """Find nearest health facility"""
    return render_template('health_facilities.html')

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account and all associated data"""
    try:
        user_id = session['user_id']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Delete all user assessments
        cursor.execute('DELETE FROM assessments WHERE user_id = ?', (user_id,))
        
        # Delete user account
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        # Clear session
        session.clear()
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to delete account: {str(e)}'})

@app.route('/profile')
@login_required
def profile():
    """User profile"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    return render_template('profile.html', user=user)

@app.route('/get_user_info')
@login_required
def get_user_info():
    """Get user information for client-side use"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT date_of_birth FROM users WHERE id = ?', (session['user_id'],))
        user_info = cursor.fetchone()
        conn.close()
        
        if user_info:
            return jsonify({
                'success': True,
                'date_of_birth': user_info[0]
            })
        else:
            return jsonify({'success': False, 'message': 'User not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_last_assessment')
@login_required
def get_last_assessment():
    """Get the user's most recent assessment data for pre-filling forms"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get the most recent assessment
        cursor.execute('''
            SELECT gender, age, hypertension, heart_disease, ever_married, 
                   work_type, residence_type, avg_glucose_level, bmi, smoking_status
            FROM assessments 
            WHERE user_id = ? 
            ORDER BY assessment_date DESC 
            LIMIT 1
        ''', (session['user_id'],))
        
        assessment = cursor.fetchone()
        conn.close()
        
        if assessment:
            return jsonify({
                'success': True,
                'assessment': {
                    'gender': assessment[0],
                    'age': assessment[1],
                    'hypertension': assessment[2],
                    'heart_disease': assessment[3],
                    'ever_married': assessment[4],
                    'work_type': assessment[5],
                    'residence_type': assessment[6],
                    'avg_glucose_level': assessment[7],
                    'bmi': assessment[8],
                    'smoking_status': assessment[9]
                }
            })
        else:
            return jsonify({'success': False, 'message': 'No previous assessments found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        data = request.get_json()
        
        # Only allow updating date_of_birth, phone, and emergency_contact
        date_of_birth = data.get('date_of_birth')
        phone = data.get('phone')
        emergency_contact = data.get('emergency_contact')
        
        # Validate emergency contact is provided
        if not emergency_contact:
            return jsonify({'success': False, 'message': 'Emergency contact is required'})
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Update user information
        cursor.execute('''
            UPDATE users 
            SET date_of_birth = ?, phone = ?, emergency_contact = ?
            WHERE id = ?
        ''', (date_of_birth, phone, emergency_contact, session['user_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Update failed: {str(e)}'})

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, password_hash, full_name FROM admin_users WHERE username = ?', (username,))
        admin = cursor.fetchone()
        
        if admin and admin[2] == hash_password(password):
            session['admin_id'] = admin[0]
            session['admin_username'] = admin[1]
            session['admin_name'] = admin[3]
            session.permanent = True
            
            # Update last login
            cursor.execute('UPDATE admin_users SET last_login = ? WHERE id = ?', 
                         (datetime.now(), admin[0]))
            conn.commit()
            conn.close()
            
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            conn.close()
            flash('Invalid admin credentials!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    session.pop('admin_name', None)
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with comprehensive system statistics"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get user statistics
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM assessments')
    total_assessments = cursor.fetchone()[0]
    
    # Get high-risk and critical cases count
    cursor.execute("SELECT COUNT(*) FROM assessments WHERE risk_level IN ('High', 'Very High')")
    high_risk_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM assessments WHERE risk_level = 'Critical'")
    critical_count = cursor.fetchone()[0]
    
    # Get risk level distribution
    cursor.execute('''
        SELECT risk_level, COUNT(*) as count 
        FROM assessments 
        GROUP BY risk_level 
        ORDER BY count DESC
    ''')
    risk_distribution = cursor.fetchall()
    
    # Get high-risk cases for follow-up
    cursor.execute('''
        SELECT a.id, u.username, u.full_name, a.age, a.risk_level, a.risk_score, a.assessment_date
        FROM assessments a
        JOIN users u ON a.user_id = u.id
        WHERE a.risk_level IN ('High', 'Very High', 'Critical')
        ORDER BY a.risk_score DESC, a.assessment_date DESC
        LIMIT 10
    ''')
    high_risk_assessments = cursor.fetchall()
    
    # Get daily assessments count
    cursor.execute('''
        SELECT COUNT(*) FROM assessments 
        WHERE DATE(assessment_date) = DATE('now')
    ''')
    daily_assessments = cursor.fetchone()[0]
    
    # Get active users this week
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM assessments 
        WHERE assessment_date >= datetime('now', '-7 days')
    ''')
    active_users_week = cursor.fetchone()[0]
    
    # Get average risk score
    cursor.execute('SELECT AVG(risk_score) FROM assessments')
    avg_risk_result = cursor.fetchone()[0]
    avg_risk_score = avg_risk_result if avg_risk_result else 0
    
    conn.close()
    
    return render_template('admin_dashboard.html',
                         admin_name=session.get('admin_name'),
                         total_users=total_users,
                         total_assessments=total_assessments,
                         high_risk_count=high_risk_count,
                         critical_count=critical_count,
                         risk_distribution=risk_distribution,
                         high_risk_assessments=high_risk_assessments,
                         daily_assessments=daily_assessments,
                         active_users_week=active_users_week,
                         avg_risk_score=avg_risk_score)

@app.route('/admin/users')
@admin_required
def admin_users():
    """Enhanced admin user management"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.username, u.full_name, u.email, u.created_at, u.last_login,
               u.is_active, u.role, COUNT(a.id) as assessment_count
        FROM users u
        LEFT JOIN assessments a ON u.id = a.user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''')
    users = cursor.fetchall()
    
    # Get admin users
    cursor.execute('''
        SELECT id, username, full_name, email, role, created_at, last_login
        FROM admin_users
        ORDER BY created_at DESC
    ''')
    admin_users = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_users.html', 
                         users=users, 
                         admin_users=admin_users,
                         admin_name=session.get('admin_name'))

@app.route('/admin/add_user', methods=['POST'])
@admin_required
def admin_add_user():
    """Admin add new user"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Hash password
        password_hash = hash_password(data['password'])
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, phone, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['username'], data['email'], password_hash, data['full_name'], 
              data.get('phone', ''), data.get('role', 'user'), 1))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/toggle_user_status/<int:user_id>', methods=['POST'])
@admin_required
def admin_toggle_user_status(user_id):
    """Admin activate/deactivate user"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get current status
        cursor.execute('SELECT is_active FROM users WHERE id = ?', (user_id,))
        current_status = cursor.fetchone()[0]
        
        # Toggle status
        new_status = 0 if current_status else 1
        cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
        
        conn.commit()
        conn.close()
        
        status_text = "activated" if new_status else "deactivated"
        return jsonify({'success': True, 'message': f'User {status_text} successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/make_admin/<int:user_id>', methods=['POST'])
@admin_required
def admin_make_admin(user_id):
    """Make user an admin"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get user details
        cursor.execute('SELECT username, email, password_hash, full_name FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            # Add to admin_users table
            cursor.execute('''
                INSERT INTO admin_users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (user[0], user[1], user[2], user[3], 'admin'))
            
            # Update user role
            cursor.execute('UPDATE users SET role = ? WHERE id = ?', ('admin', user_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'User promoted to admin successfully'})
        else:
            return jsonify({'success': False, 'message': 'User not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/assessments')
@admin_required
def admin_assessments():
    """Enhanced admin assessment management with analytics"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get all assessments
    cursor.execute('''
        SELECT a.id, u.username, u.full_name, a.age, a.risk_level, a.risk_score, 
               a.assessment_date, a.hypertension, a.heart_disease, a.avg_glucose_level,
               a.bmi, a.smoking_status, a.work_type, a.gender
        FROM assessments a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.assessment_date DESC
    ''')
    assessments = cursor.fetchall()
    
    # Analyze stroke causes
    stroke_causes = {
        'hypertension': 0,
        'heart_disease': 0,
        'high_glucose': 0,
        'obesity': 0,
        'smoking': 0,
        'age_related': 0
    }
    
    total_assessments = len(assessments)
    
    for assessment in assessments:
        if assessment[7]:  # hypertension
            stroke_causes['hypertension'] += 1
        if assessment[8]:  # heart_disease
            stroke_causes['heart_disease'] += 1
        if assessment[9] > 200:  # high glucose
            stroke_causes['high_glucose'] += 1
        if assessment[10] > 30:  # obesity (BMI > 30)
            stroke_causes['obesity'] += 1
        if assessment[11] in ['smokes', 'formerly smoked']:  # smoking
            stroke_causes['smoking'] += 1
        if assessment[3] > 65:  # age related
            stroke_causes['age_related'] += 1
    
    # Convert to percentages
    if total_assessments > 0:
        for cause in stroke_causes:
            stroke_causes[cause] = round((stroke_causes[cause] / total_assessments) * 100, 1)
    
    # Get risk level distribution
    cursor.execute('''
        SELECT risk_level, COUNT(*) as count
        FROM assessments
        GROUP BY risk_level
        ORDER BY count DESC
    ''')
    risk_distribution = cursor.fetchall()
    
    # Get assessment templates
    cursor.execute('''
        SELECT id, name, description, is_active, created_at
        FROM assessment_templates
        ORDER BY created_at DESC
    ''')
    templates = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_assessments.html', 
                         assessments=assessments,
                         stroke_causes=stroke_causes,
                         risk_distribution=risk_distribution,
                         templates=templates,
                         total_assessments=total_assessments,
                         admin_name=session.get('admin_name'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Admin delete user"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Delete user's assessments first
        cursor.execute('DELETE FROM assessments WHERE user_id = ?', (user_id,))
        
        # Delete user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to delete user: {str(e)}'})

@app.route('/admin/user_activity')
@admin_required
def admin_user_activity():
    """Admin view user activity logs"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.username, u.full_name, u.last_login, 
               COUNT(a.id) as assessment_count,
               MAX(a.assessment_date) as last_assessment
        FROM users u
        LEFT JOIN assessments a ON u.id = a.user_id
        GROUP BY u.id
        ORDER BY u.last_login DESC NULLS LAST
    ''')
    user_activity = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_user_activity.html', 
                         user_activity=user_activity,
                         admin_name=session.get('admin_name'))

@app.route('/admin/deactivated_users')
@admin_required
def admin_deactivated_users():
    """Admin view deactivated users (placeholder for future implementation)"""
    return render_template('admin_deactivated_users.html',
                         admin_name=session.get('admin_name'))

@app.route('/admin/high_risk_cases')
@admin_required
def admin_high_risk_cases():
    """Admin view high-risk cases requiring follow-up"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.id, u.username, u.full_name, u.email, a.age, a.gender,
               a.risk_level, a.risk_score, a.assessment_date, a.risk_factors,
               a.hypertension, a.heart_disease, a.avg_glucose_level, a.bmi
        FROM assessments a
        JOIN users u ON a.user_id = u.id
        WHERE a.risk_level IN ('High', 'Very High', 'Critical')
        ORDER BY a.risk_score DESC, a.assessment_date DESC
    ''')
    high_risk_cases = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_high_risk_cases.html',
                         high_risk_cases=high_risk_cases,
                         admin_name=session.get('admin_name'))

@app.route('/admin/data_export')
@admin_required
def admin_data_export():
    """Admin data export functionality"""
    return render_template('admin_data_export.html',
                         admin_name=session.get('admin_name'))

@app.route('/admin/system_settings')
@admin_required
def admin_system_settings():
    """Admin system configuration"""
    return render_template('admin_system_settings.html',
                         admin_name=session.get('admin_name'))

@app.route('/admin/recommendations')
@admin_required
def admin_recommendations():
    """Admin manage recommendation templates"""
    return render_template('admin_recommendations.html',
                         admin_name=session.get('admin_name'))

@app.route('/admin/reports')
@admin_required
def admin_reports():
    """Admin report management"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get assessment reports data
    cursor.execute('''
        SELECT a.id, u.username, u.full_name, a.risk_level, a.risk_score, 
               a.assessment_date, 'PDF Report' as report_type
        FROM assessments a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.assessment_date DESC
    ''')
    reports = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_reports.html',
                         reports=reports,
                         admin_name=session.get('admin_name'))

@app.route('/admin/login_logs')
@admin_required
def admin_login_logs():
    """Admin view login audit trail"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get user login history
    cursor.execute('''
        SELECT u.id, u.username, u.full_name, u.last_login, u.created_at,
               COUNT(a.id) as total_assessments
        FROM users u
        LEFT JOIN assessments a ON u.id = a.user_id
        GROUP BY u.id
        ORDER BY u.last_login DESC NULLS LAST
    ''')
    login_logs = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_login_logs.html',
                         login_logs=login_logs,
                         admin_name=session.get('admin_name'))

@app.route('/admin/system_logs')
@admin_required
def admin_system_logs():
    """Admin view system activity logs"""
    return render_template('admin_system_logs.html',
                         admin_name=session.get('admin_name'))

@app.route('/admin/feedback')
@admin_required
def admin_feedback():
    """Enhanced admin view user feedback"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT f.id, f.subject, f.message, f.category, f.status, f.created_at,
               u.username, u.full_name, f.admin_response, f.responded_at,
               au.full_name as responded_by_name
        FROM user_feedback f
        JOIN users u ON f.user_id = u.id
        LEFT JOIN admin_users au ON f.responded_by = au.id
        ORDER BY f.created_at DESC
    ''')
    feedback_list = cursor.fetchall()
    
    # Get feedback statistics
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM user_feedback
        GROUP BY status
    ''')
    feedback_stats = dict(cursor.fetchall())
    
    conn.close()
    
    return render_template('admin_feedback.html',
                         feedback_list=feedback_list,
                         feedback_stats=feedback_stats,
                         admin_name=session.get('admin_name'))

@app.route('/admin/mark_followed_up/<int:assessment_id>', methods=['POST'])
@admin_required
def admin_mark_followed_up(assessment_id):
    """Mark high-risk case as followed up"""
    try:
        # In a real implementation, you would add a follow_up_status column to assessments table
        # For now, we'll just return success
        return jsonify({'success': True, 'message': 'Case marked as followed up'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to update follow-up status: {str(e)}'})

# Template Management Routes
@app.route('/admin/templates')
@admin_required
def admin_templates():
    """Admin manage assessment templates"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.id, t.name, t.description, t.is_active, t.created_at,
               a.full_name as created_by_name
        FROM assessment_templates t
        JOIN admin_users a ON t.created_by = a.id
        ORDER BY t.created_at DESC
    ''')
    templates = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_templates.html',
                         templates=templates,
                         admin_name=session.get('admin_name'))

@app.route('/admin/add_template', methods=['POST'])
@admin_required
def admin_add_template():
    """Add new assessment template"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO assessment_templates (name, description, template_data, created_by)
            VALUES (?, ?, ?, ?)
        ''', (data['name'], data['description'], data['template_data'], session['admin_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Template added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/edit_template/<int:template_id>', methods=['POST'])
@admin_required
def admin_edit_template(template_id):
    """Edit assessment template"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE assessment_templates 
            SET name = ?, description = ?, template_data = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (data['name'], data['description'], data['template_data'], template_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Template updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/toggle_template/<int:template_id>', methods=['POST'])
@admin_required
def admin_toggle_template(template_id):
    """Toggle template active status"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT is_active FROM assessment_templates WHERE id = ?', (template_id,))
        current_status = cursor.fetchone()[0]
        new_status = 0 if current_status else 1
        
        cursor.execute('UPDATE assessment_templates SET is_active = ? WHERE id = ?', (new_status, template_id))
        
        conn.commit()
        conn.close()
        
        status_text = "activated" if new_status else "deactivated"
        return jsonify({'success': True, 'message': f'Template {status_text} successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Announcements Management Routes
@app.route('/admin/announcements')
@admin_required
def admin_announcements():
    """Admin manage system announcements"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.id, a.title, a.content, a.type, a.is_active, a.created_at, a.expires_at,
               au.full_name as created_by_name
        FROM announcements a
        JOIN admin_users au ON a.created_by = au.id
        ORDER BY a.created_at DESC
    ''')
    announcements = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_announcements.html',
                         announcements=announcements,
                         admin_name=session.get('admin_name'))

@app.route('/admin/add_announcement', methods=['POST'])
@admin_required
def admin_add_announcement():
    """Add new system announcement"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO announcements (title, content, type, created_by, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['title'], data['content'], data['type'], session['admin_id'], data.get('expires_at')))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Announcement added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/toggle_announcement/<int:announcement_id>', methods=['POST'])
@admin_required
def admin_toggle_announcement(announcement_id):
    """Toggle announcement active status"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT is_active FROM announcements WHERE id = ?', (announcement_id,))
        current_status = cursor.fetchone()[0]
        new_status = 0 if current_status else 1
        
        cursor.execute('UPDATE announcements SET is_active = ? WHERE id = ?', (new_status, announcement_id))
        
        conn.commit()
        conn.close()
        
        status_text = "published" if new_status else "unpublished"
        return jsonify({'success': True, 'message': f'Announcement {status_text} successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# User Feedback Submission Route
@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    """User submit feedback"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_feedback (user_id, subject, message, category)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], data['subject'], data['message'], data['category']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Feedback submitted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/respond_feedback/<int:feedback_id>', methods=['POST'])
@admin_required
def admin_respond_feedback(feedback_id):
    """Admin respond to user feedback"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_feedback 
            SET admin_response = ?, status = 'responded', responded_by = ?, responded_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (data['response'], session['admin_id'], feedback_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Response sent successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Get active announcements for users
@app.route('/get_announcements')
@login_required
def get_announcements():
    """Get active announcements for users (ignore expiration for now)"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, content, type
        FROM announcements
        WHERE is_active = 1
        ORDER BY created_at DESC
        LIMIT 5
    ''')
    announcements = cursor.fetchall()
    
    conn.close()
    
    return jsonify([{
        'title': ann[0],
        'content': ann[1],
        'type': ann[2]
    } for ann in announcements])

@app.route('/check_user_status')
@login_required
def check_user_status():
    """Check if current user is still active"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT is_active FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[0]:
        return jsonify({'active': True})
    else:
        return jsonify({'active': False, 'user_id': session.get('user_id')})

@app.route('/admin/quick_reactivate_user', methods=['POST'])
@admin_required
def admin_quick_reactivate_user():
    """Quick reactivate user by username"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Find and reactivate user
        cursor.execute('UPDATE users SET is_active = 1 WHERE username = ?', (username,))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': f'User {username} reactivated successfully'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    # Ensure database directory exists
    db_dir = os.path.dirname(DATABASE)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Initialize database
    init_database()
    
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    app.run(debug=True, host='127.0.0.1', port=5001)
