from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, IntegerField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional
from datetime import datetime, date
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///blood_donation.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Database Models
class Donor(db.Model):
    __tablename__ = 'donors'
    donor_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    last_donation_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    donations = db.relationship('Donation', backref='donor', lazy=True)

class Recipient(db.Model):
    __tablename__ = 'recipients'
    recipient_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    request_status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    requests = db.relationship('BloodRequest', backref='recipient', lazy=True)

class BloodRequest(db.Model):
    __tablename__ = 'blood_requests'
    request_id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipients.recipient_id'), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    quantity_needed_ml = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Donation(db.Model):
    __tablename__ = 'donations'
    donation_id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.donor_id'), nullable=False)
    donation_date = db.Column(db.Date, nullable=False)
    blood_volume_ml = db.Column(db.Integer, nullable=False)
    hospital = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BloodInventory(db.Model):
    __tablename__ = 'blood_inventory'
    inventory_id = db.Column(db.Integer, primary_key=True)
    blood_group = db.Column(db.String(5), unique=True, nullable=False)
    total_units = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Forms
class DonorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=18, max=100)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Other')], validators=[DataRequired()])
    blood_group = SelectField('Blood Group', choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address = TextAreaField('Address', validators=[DataRequired(), Length(max=500)])
    last_donation_date = DateField('Last Donation Date', validators=[Optional()])

class RecipientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1, max=120)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    blood_group = SelectField('Blood Group', choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address = TextAreaField('Address', validators=[DataRequired(), Length(max=500)])
    request_status = SelectField('Request Status', choices=[
        ('Pending', 'Pending'), ('Approved', 'Approved'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')
    ], validators=[DataRequired()])

class DonationForm(FlaskForm):
    donor_id = SelectField('Donor', coerce=int, validators=[DataRequired()])
    donation_date = DateField('Donation Date', validators=[DataRequired()])
    blood_volume_ml = IntegerField('Blood Volume (ml)', validators=[DataRequired(), NumberRange(min=100, max=500)])
    hospital = StringField('Hospital', validators=[DataRequired(), Length(max=100)])

class BloodRequestForm(FlaskForm):
    recipient_id = SelectField('Recipient', coerce=int, validators=[DataRequired()])
    blood_group = SelectField('Blood Group', choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], validators=[DataRequired()])
    quantity_needed_ml = IntegerField('Quantity Needed (ml)', validators=[DataRequired(), NumberRange(min=100, max=2000)])

# Routes
@app.route('/')
def home():
    try:
        # Get summary statistics
        total_donors = Donor.query.count()
        total_recipients = Recipient.query.count()
        total_donations = Donation.query.count()
        total_requests = BloodRequest.query.count()
        
        # Get recent donations
        recent_donations = Donation.query.order_by(Donation.created_at.desc()).limit(5).all()
        
        # Get blood inventory summary
        inventory = BloodInventory.query.all()
        
        return render_template('index.html', 
                             total_donors=total_donors,
                             total_recipients=total_recipients,
                             total_donations=total_donations,
                             total_requests=total_requests,
                             recent_donations=recent_donations,
                             inventory=inventory)
    except Exception as e:
        # For demo purposes, show sample data when database is not available
        return render_template('index.html', 
                             total_donors=0,
                             total_recipients=0,
                             total_donations=0,
                             total_requests=0,
                             recent_donations=[],
                             inventory=[])

@app.route('/donor/view')
def view_donors():
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        
        query = Donor.query
        if search:
            query = query.filter(
                db.or_(
                    Donor.name.ilike(f'%{search}%'),
                    Donor.blood_group.ilike(f'%{search}%'),
                    Donor.email.ilike(f'%{search}%')
                )
            )
        
        donors = query.order_by(Donor.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        
        return render_template('donor.html', donors=donors, search=search)
    except Exception as e:
        flash(f'Error loading donors: {str(e)}', 'error')
        return redirect(url_for('home'))

@app.route('/donor/add', methods=['GET', 'POST'])
def add_donor():
    form = DonorForm()
    
    if form.validate_on_submit():
        try:
            donor = Donor(
                name=form.name.data,
                age=form.age.data,
                gender=form.gender.data,
                blood_group=form.blood_group.data,
                phone=form.phone.data,
                email=form.email.data,
                address=form.address.data,
                last_donation_date=form.last_donation_date.data
            )
            
            db.session.add(donor)
            db.session.commit()
            
            flash('Donor added successfully!', 'success')
            return redirect(url_for('view_donors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding donor: {str(e)}', 'error')
    
    return render_template('adddonor.html', form=form)

@app.route('/donor/edit/<int:id>', methods=['GET', 'POST'])
def edit_donor(id):
    try:
        donor = Donor.query.get_or_404(id)
        form = DonorForm(obj=donor)
        
        if form.validate_on_submit():
            donor.name = form.name.data
            donor.age = form.age.data
            donor.gender = form.gender.data
            donor.blood_group = form.blood_group.data
            donor.phone = form.phone.data
            donor.email = form.email.data
            donor.address = form.address.data
            donor.last_donation_date = form.last_donation_date.data
            
            db.session.commit()
            flash('Donor updated successfully!', 'success')
            return redirect(url_for('view_donors'))
        
        return render_template('editdonor.html', form=form, donor=donor)
    except Exception as e:
        flash(f'Error editing donor: {str(e)}', 'error')
        return redirect(url_for('view_donors'))

@app.route('/donor/delete/<int:id>')
def delete_donor(id):
    try:
        donor = Donor.query.get_or_404(id)
        
        # Check if donor has donations
        if donor.donations:
            flash('Cannot delete donor with existing donations', 'error')
            return redirect(url_for('view_donors'))
        
        db.session.delete(donor)
        db.session.commit()
        flash('Donor deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting donor: {str(e)}', 'error')
    
    return redirect(url_for('view_donors'))

@app.route('/recipient/view')
def view_recipients():
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        
        query = Recipient.query
        if search:
            query = query.filter(
                db.or_(
                    Recipient.name.ilike(f'%{search}%'),
                    Recipient.blood_group.ilike(f'%{search}%'),
                    Recipient.request_status.ilike(f'%{search}%')
                )
            )
        
        recipients = query.order_by(Recipient.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        
        return render_template('recipient.html', recipients=recipients, search=search)
    except Exception as e:
        flash(f'Error loading recipients: {str(e)}', 'error')
        return redirect(url_for('home'))

@app.route('/recipient/add', methods=['GET', 'POST'])
def add_recipient():
    form = RecipientForm()
    
    if form.validate_on_submit():
        try:
            recipient = Recipient(
                name=form.name.data,
                age=form.age.data,
                gender=form.gender.data,
                blood_group=form.blood_group.data,
                phone=form.phone.data,
                email=form.email.data,
                address=form.address.data,
                request_status=form.request_status.data
            )
            
            db.session.add(recipient)
            db.session.commit()
            
            flash('Recipient added successfully!', 'success')
            return redirect(url_for('view_recipients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding recipient: {str(e)}', 'error')
    
    return render_template('add_recipient.html', form=form)

@app.route('/recipient/edit/<int:id>', methods=['GET', 'POST'])
def edit_recipient(id):
    try:
        recipient = Recipient.query.get_or_404(id)
        form = RecipientForm(obj=recipient)
        
        if form.validate_on_submit():
            recipient.name = form.name.data
            recipient.age = form.age.data
            recipient.gender = form.gender.data
            recipient.blood_group = form.blood_group.data
            recipient.phone = form.phone.data
            recipient.email = form.email.data
            recipient.address = form.address.data
            recipient.request_status = form.request_status.data
            
            db.session.commit()
            flash('Recipient updated successfully!', 'success')
            return redirect(url_for('view_recipients'))
        
        return render_template('edit_recipient.html', form=form, recipient=recipient)
    except Exception as e:
        flash(f'Error editing recipient: {str(e)}', 'error')
        return redirect(url_for('view_recipients'))

@app.route('/recipient/delete/<int:id>')
def delete_recipient(id):
    try:
        recipient = Recipient.query.get_or_404(id)
        
        # Check if recipient has requests
        if recipient.requests:
            flash('Cannot delete recipient with existing blood requests', 'error')
            return redirect(url_for('view_recipients'))
        
        db.session.delete(recipient)
        db.session.commit()
        flash('Recipient deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting recipient: {str(e)}', 'error')
    
    return redirect(url_for('view_recipients'))

@app.route('/requests/view')
def view_requests():
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', '')
        
        query = BloodRequest.query.join(Recipient)
        if status_filter:
            query = query.filter(BloodRequest.status == status_filter)
        
        requests = query.order_by(BloodRequest.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        
        return render_template('requests.html', requests=requests, status_filter=status_filter)
    except Exception as e:
        flash(f'Error loading requests: {str(e)}', 'error')
        return redirect(url_for('home'))

@app.route('/requests/add', methods=['GET', 'POST'])
def add_request():
    form = BloodRequestForm()
    form.recipient_id.choices = [(r.recipient_id, r.name) for r in Recipient.query.all()]
    
    if form.validate_on_submit():
        try:
            request_obj = BloodRequest(
                recipient_id=form.recipient_id.data,
                blood_group=form.blood_group.data,
                quantity_needed_ml=form.quantity_needed_ml.data
            )
            
            db.session.add(request_obj)
            db.session.commit()
            
            flash('Blood request added successfully!', 'success')
            return redirect(url_for('view_requests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding request: {str(e)}', 'error')
    
    return render_template('add_request.html', form=form)

@app.route('/requests/edit/<int:request_id>', methods=['GET', 'POST'])
def edit_request(request_id):
    try:
        request_obj = BloodRequest.query.get_or_404(request_id)
        
        if request.method == 'POST':
            status = request.form.get('status')
            if status in ['Pending', 'Approved', 'Completed', 'Cancelled']:
                request_obj.status = status
                db.session.commit()
                flash('Request status updated successfully!', 'success')
                return redirect(url_for('view_requests'))
        
        return render_template('edit_request.html', request_data=request_obj)
    except Exception as e:
        flash(f'Error editing request: {str(e)}', 'error')
        return redirect(url_for('view_requests'))

@app.route('/requests/delete/<int:request_id>')
def delete_request(request_id):
    try:
        request_obj = BloodRequest.query.get_or_404(request_id)
        db.session.delete(request_obj)
        db.session.commit()
        flash('Request deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting request: {str(e)}', 'error')
    
    return redirect(url_for('view_requests'))

@app.route('/donations/view')
def view_donations():
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        
        query = Donation.query.join(Donor)
        if search:
            query = query.filter(
                db.or_(
                    Donor.name.ilike(f'%{search}%'),
                    Donor.blood_group.ilike(f'%{search}%')
                )
            )
        
        donations = query.order_by(Donation.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        
        return render_template('donations.html', donations=donations, search=search)
    except Exception as e:
        flash(f'Error loading donations: {str(e)}', 'error')
        return redirect(url_for('home'))

@app.route('/donations/add', methods=['GET', 'POST'])
def add_donation():
    form = DonationForm()
    form.donor_id.choices = [(d.donor_id, d.name) for d in Donor.query.all()]
    
    if form.validate_on_submit():
        try:
            donation = Donation(
                donor_id=form.donor_id.data,
                donation_date=form.donation_date.data,
                blood_volume_ml=form.blood_volume_ml.data,
                hospital=form.hospital.data
            )
            
            # Update donor's last donation date
            donor = Donor.query.get(form.donor_id.data)
            donor.last_donation_date = form.donation_date.data
            
            # Update blood inventory
            donor_obj = Donor.query.get(form.donor_id.data)
            inventory = BloodInventory.query.filter_by(blood_group=donor_obj.blood_group).first()
            
            if inventory:
                inventory.total_units += form.blood_volume_ml.data // 450  # Convert ml to units
            else:
                inventory = BloodInventory(
                    blood_group=donor_obj.blood_group,
                    total_units=form.blood_volume_ml.data // 450
                )
                db.session.add(inventory)
            
            db.session.add(donation)
            db.session.commit()
            
            flash('Donation added successfully!', 'success')
            return redirect(url_for('view_donations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding donation: {str(e)}', 'error')
    
    return render_template('add_donation.html', form=form)

@app.route('/donations/edit/<int:id>', methods=['GET', 'POST'])
def edit_donation(id):
    try:
        donation = Donation.query.get_or_404(id)
        form = DonationForm(obj=donation)
        form.donor_id.choices = [(d.donor_id, d.name) for d in Donor.query.all()]
        
        if form.validate_on_submit():
            donation.donor_id = form.donor_id.data
            donation.donation_date = form.donation_date.data
            donation.blood_volume_ml = form.blood_volume_ml.data
            donation.hospital = form.hospital.data
            
            db.session.commit()
            flash('Donation updated successfully!', 'success')
            return redirect(url_for('view_donations'))
        
        return render_template('edit_donation.html', form=form, donation=donation)
    except Exception as e:
        flash(f'Error editing donation: {str(e)}', 'error')
        return redirect(url_for('view_donations'))

@app.route('/donations/delete/<int:id>')
def delete_donation(id):
    try:
        donation = Donation.query.get_or_404(id)
        db.session.delete(donation)
        db.session.commit()
        flash('Donation deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting donation: {str(e)}', 'error')
    
    return redirect(url_for('view_donations'))

@app.route('/blood_inventory')
def blood_inventory():
    try:
        inventory = BloodInventory.query.order_by(BloodInventory.blood_group).all()
        return render_template('inventory.html', inventory=inventory)
    except Exception as e:
        flash(f'Error loading inventory: {str(e)}', 'error')
        return redirect(url_for('home'))

@app.route('/update_inventory', methods=['GET', 'POST'])
def update_inventory():
    if request.method == 'POST':
        try:
            blood_group = request.form.get('blood_group')
            units = int(request.form.get('units', 0))
            
            if units < 0:
                flash('Units cannot be negative', 'error')
                return redirect(url_for('update_inventory'))
            
            inventory = BloodInventory.query.filter_by(blood_group=blood_group).first()
            
            if inventory:
                inventory.total_units += units
            else:
                inventory = BloodInventory(blood_group=blood_group, total_units=units)
                db.session.add(inventory)
            
            db.session.commit()
            flash('Inventory updated successfully!', 'success')
            return redirect(url_for('blood_inventory'))
        except Exception as e:
            flash(f'Error updating inventory: {str(e)}', 'error')
    
    return render_template('update_inventory.html')

@app.route('/api/stats')
def api_stats():
    try:
        stats = {
            'total_donors': Donor.query.count(),
            'total_recipients': Recipient.query.count(),
            'total_donations': Donation.query.count(),
            'total_requests': BloodRequest.query.count(),
            'blood_inventory': {inv.blood_group: inv.total_units for inv in BloodInventory.query.all()}
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("📱 Running in demo mode - templates will show sample data")
    
    print("🚀 Starting Flask application...")
    print("🌐 Open your browser and go to: http://localhost:5000")
    app.run(debug=True)
