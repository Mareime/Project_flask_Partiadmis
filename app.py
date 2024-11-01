import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bd_interventions.sqlite3'
db = SQLAlchemy(app)

class Intervenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    poste = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    interventions = db.relationship('Intervention', backref='intervenant', lazy=True)

    def __init__(self, nom, prenom, poste, email, password):
        self.nom = nom
        self.prenom = prenom
        self.poste = poste
        self.email = email
        self.password = password

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    direction = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    interventions = db.relationship('Intervention', backref='client', lazy=True)

    def __init__(self, nom, prenom, direction, email, password):
        self.nom = nom
        self.prenom = prenom
        self.direction = direction
        self.email = email
        self.password = password

class Intervention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # "Soft" or "Hard"
    motive = db.Column(db.String(200), nullable=False)
    etat = db.Column(db.String(50), nullable=False)  # "en attente" or "réalisée"
    
    id_intervenant = db.Column(db.Integer, db.ForeignKey('intervenant.id'), nullable=False)
    id_client = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

    def __init__(self, date, type, motive, etat, id_intervenant, id_client):
        self.date = date
        self.type = type
        self.motive = motive
        self.etat = etat
        self.id_intervenant = id_intervenant
        self.id_client = id_client

class Administrateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __init__(self, email, password):
        self.email = email
        self.password = password


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'client_id' not in session and 'admin_id' not in session:
            flash("Vous devez être connecté pour accéder à cette page.", "danger")
            return redirect(url_for('login_client'))
        return f(*args, **kwargs)
    return decorated_function
@app.route("/", methods=["GET", "POST"])
def login_client():
    if request.method == "POST":
        mail = request.form['email']
        password = request.form['password']
        
        # Check if the user is a client
        client = Client.query.filter_by(email=mail).first()
        if client and client.password == password:
            session['client_id'] = client.id

            return redirect(url_for('accueil_client', id=client.id))
        
        # Check if the user is an administrator
        admin = Administrateur.query.filter_by(email=mail).first()
        if admin and admin.password == password:
            session['admin_id'] = admin.id  # Store admin ID in session
            return redirect(url_for('dashbord'))  # Redirect to the dashboard
        
        flash("Email ou mot de passe incorrect. Veuillez réessayer.", "danger")
    
    return render_template("login.html")


@app.route('/sunup')
def sunup():
    return render_template("sunup.html")


@app.route("/ajoute_client", methods=["POST", "GET"])
def ajoute_client():
    if request.method == "POST":
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        direction = request.form.get("direction")
        email = request.form.get("email")
        password = request.form.get("password")

        if not nom or not prenom or not direction or not email or not password:
            flash("Tous les champs doivent être remplis.", "danger")
            return render_template("ajouter_client.html")

        existing_client = Client.query.filter_by(email=email).first()
        if existing_client:
            flash("Cet email est déjà utilisé. Veuillez en choisir un autre.", "danger")
            return render_template("ajouter_client.html")

        new_client = Client(
            nom=nom,
            prenom=prenom,
            direction=direction,
            email=email,
            password=password # Hash the password
        )
        
        db.session.add(new_client)
        db.session.commit()
        flash("Client ajouté avec succès!", "success")
        return redirect(url_for('accueil_client', id=new_client.id)) 

    return render_template("ajouter_client.html")  

@app.route("/accueil_client/<int:id>")
@login_required
def accueil_client(id):
    intervenants = Intervenant.query.all()
    client = Client.query.get_or_404(id)
    return render_template("accueil_client.html", client=client, intervenants=intervenants)

@app.route("/dashbord")
@login_required
def dashbord():
    # Retrieve the admin ID from the session if needed
    admin_id = session.get('admin_id')
    # Fetch data as needed for the dashboard
    clients = Client.query.all()  
    intervenants = Intervenant.query.all()  
    interventions = Intervention.query.all()
    return render_template("dashbord.html", clients=clients, intervenants=intervenants, interventions=interventions, admin_id=admin_id)

@app.route("/edit_client/<int:id>", methods=["GET", "POST"])
@login_required
def edit_client(id):
    client = Client.query.get_or_404(id)
    
    if request.method == "POST":
        # Update client information from the form
        client.nom = request.form.get("nom")
        client.prenom = request.form.get("prenom")
        client.direction = request.form.get("direction")
        client.email = request.form.get("email")
        client.password = request.form.get("password")

        db.session.commit()
        flash("Client mis à jour avec succès!", "success")
        return redirect(url_for('dashbordClient'))  # Redirect to the dashboard after update

    return render_template("edit_client.html", client=client)



@app.route("/delete_client/<int:id>", methods=["POST"])
@login_required
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash("Client supprimé avec succès!", "success")
    return redirect(url_for('dashbordClient'))

@app.route("/dashbordIntervenant")
@login_required
def dashbordIntervenant():
    intervenants = Intervenant.query.all()
    clients = Client.query.all()
    interventions = Intervention.query.all()
    return render_template("dashbordIntervenant.html", intervenants=intervenants, clients=clients, interventions=interventions)

@app.route('/edit_intervenant/<int:id>', methods=['POST'])
@login_required
def edit_intervenant(id):
    intervenant = Intervenant.query.get_or_404(id)
    
    intervenant.nom = request.form['nom']
    intervenant.prenom = request.form['prenom']
    intervenant.poste = request.form['poste']
    intervenant.email = request.form['email']
    
    # Only update password if provided
    password = request.form['password']
    if password:
        intervenant.password = generate_password_hash(password)
    
    db.session.commit()
    flash('Intervenant mis à jour avec succès!', 'success')
    return redirect(url_for('dashbordIntervenant'))

@app.route('/delete_intervenants/<int:id>', methods=['POST'])
@login_required
def delete_intervenants(id):
    intervenant = Intervenant.query.get_or_404(id)
    db.session.delete(intervenant)
    db.session.commit()
    flash('Intervenant supprimé avec succès!', 'success')
    return redirect(url_for('dashbordIntervenant'))

@app.route('/add_intervenant', methods=['POST'])
@login_required
def add_intervenant():
    nom = request.form['nom']
    prenom = request.form['prenom']
    poste = request.form['poste']
    email = request.form['email']
    password = request.form['password']
    
    existing_intervenant = Intervenant.query.filter_by(email=email).first()
    if existing_intervenant:
        flash("Cet email est déjà utilisé pour un intervenant.", "danger")
        return redirect(url_for('dashbordIntervenant'))

    new_intervenant = Intervenant(
        nom=nom,
        prenom=prenom,
        poste=poste,
        email=email,
        password=password  # Hash the password
    )
    
    db.session.add(new_intervenant)
    db.session.commit()
    flash("Intervenant ajouté avec succès!", "success")
    return redirect(url_for('dashbordIntervenant'))

@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    session.pop('client_id', None)  # Supprimer également l'ID du client
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for('login_client'))  # Redirige vers la page de connexion

@app.route("/dashbordClient")
@login_required
def dashbordClient():
    if id:
        intervenants = Intervenant.query.all()
        clients = Client.query.all()
        interventions = Intervention.query.all()
        return render_template('dashbordClient.html', intervenants=intervenants, clients=clients)


@app.route("/dashbordIntervation")
@login_required
def dashbordIntervation():
    interventions = Intervention.query.all()
    intervenants = Intervenant.query.all()
    clients = Client.query.all()
    return render_template('dashbordIntervation.html', interventions=interventions,intervenants=intervenants,clients=clients)

@app.route('/create_intervention', methods=['POST'])
@login_required
def create_intervention():
    date_str = request.form['date']  # Get the date string from the form
    type_intervention = request.form['type']
    motive = request.form['motive']
    intervenant_id = request.form['intervenant_id']
    client_id = session.get('client_id')  # Assuming the client is logged in

    # Convert the string to a datetime object
    try:
        date = datetime.fromisoformat(date_str)  # Adjust format if needed
    except ValueError:
        flash("Format de date invalide. Veuillez entrer une date correcte.", "danger")
        return redirect(url_for('accueil_client', id=client_id))

    # Ensure client_id is set
    if client_id is None:
        flash("Client non connecté. Veuillez vous connecter pour créer une intervention.", "danger")
        return redirect(url_for('login_client'))

    # Create a new intervention
    new_intervention = Intervention(
        date=date,
        type=type_intervention,
        motive=motive,
        etat='en attente',  # Initial state
        id_intervenant=intervenant_id,
        id_client=client_id
    )

    db.session.add(new_intervention)
    db.session.commit()
    flash("Intervention créée avec succès!", "success")

    return redirect(url_for('accueil_client', id=client_id))  # Redirect to client's home page


@app.route('/update_intervention_state/<int:id>', methods=['POST'])
@login_required
def update_intervention_state(id):
    intervention = Intervention.query.get_or_404(id)
    new_state = request.form['etat']
    
    intervention.etat = new_state
    db.session.commit()
    
    flash("État de l'intervention mis à jour avec succès!", "success")
    return redirect(url_for('dashbordIntervation'))  # Redirect to the interventions dashboard

@app.route("/graphe")
def graphe():
    clients = Client.query.all()  
    intervenants = Intervenant.query.all()  
    interventions = Intervention.query.all()
    return render_template("graphe.html",clients=clients,intervenants=intervenants,interventions=interventions)

@app.route('/data/dashboard')
@login_required
def data_dashboard():
    tasks = {
        'realisees': Intervention.query.filter_by(etat='réalisée').count(),
        'en_attente': Intervention.query.filter_by(etat='en attente').count()
    }
    
    # Calculate tasks by intervenant
    intervenants_data = db.session.query(Intervenant.nom, db.func.count(Intervention.id)).join(Intervention).group_by(Intervenant.nom).all()
    intervenants_dict = {nom: count for nom, count in intervenants_data}
    
    return {
        'tasks': tasks,
        'intervenants': intervenants_dict
    }

@app.route('/edit_intervention/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_intervention(id):
    intervention = Intervention.query.get_or_404(id)
    
    if request.method == 'POST':
        intervention.date = request.form['date']
        intervention.type = request.form['type']
        intervention.motive = request.form['motive']
        intervention.etat = request.form['etat']
        intervention.id_intervenant = request.form['intervenant_id']
        intervention.id_client = request.form['client_id']  

        db.session.commit()
        flash("Intervention mise à jour avec succès!", "success")
        return redirect(url_for('dashbordIntervation'))

    return render_template("edit_intervention.html", intervention=intervention)
@app.route('/delete_intervention/<int:id>', methods=['POST'])
@login_required
def delete_intervention(id):
    intervention = Intervention.query.get_or_404(id)
    db.session.delete(intervention)
    db.session.commit()
    flash("Intervention supprimée avec succès!", "success")
    return redirect(url_for('dashbordIntervation'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
