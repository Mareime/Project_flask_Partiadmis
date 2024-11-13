import datetime
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime
import base64
import matplotlib.pyplot as plt
from flask import Flask, render_template, Response
from io import BytesIO
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
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
        
        intervenant=Intervenant.query.filter_by(email=mail).first()
        if intervenant and intervenant.password == password:
            session['intervenant_id'] = intervenant.id
            return redirect(url_for('accueil_intervenant',id=intervenant.id))
        client = Client.query.filter_by(email=mail).first()
        if client and client.password == password:
            session['client_id'] = client.id

            return redirect(url_for('accueil_client', id=client.id))
        
       
        admin = Administrateur.query.filter_by(email=mail).first()
        if admin and admin.password == password:
            session['admin_id'] = admin.id  
            return redirect(url_for('dashbord'))  
        
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
            password=password 
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
# les intervation cree par ces clients
@app.route("/interventions_client/<int:id>")
def Intervation_client(id):
    intervation = Intervention.query.all(id_client=id)
    return render_template("interventions_client.html", intervation=intervation)
# 
@app.route("/dashbord")
@login_required
def dashbord():
  
    admin_id = session.get('admin_id')

    clients = Client.query.all()  
    intervenants = Intervenant.query.all()  
    interventions = Intervention.query.all()
    return render_template("dashbord.html", clients=clients, intervenants=intervenants, interventions=interventions, admin_id=admin_id)

@app.route("/edit_client/<int:id>", methods=["GET", "POST"])
@login_required
def edit_client(id):
    client = Client.query.get_or_404(id)
    
    if request.method == "POST":
        
        client.nom = request.form.get("nom")
        client.prenom = request.form.get("prenom")
        client.direction = request.form.get("direction")
        client.email = request.form.get("email")
        client.password = request.form.get("password")

        db.session.commit()
        flash("Client mis à jour avec succès!", "success")
        return redirect(url_for('dashbordClient'))  

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
    intervenant.password = request.form['password']
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
        password=password  
    )
    
    db.session.add(new_intervenant)
    db.session.commit()
    flash("Intervenant ajouté avec succès!", "success")
    return redirect(url_for('dashbordIntervenant'))

@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    session.pop('client_id', None)  
    session.pop('intervenant_id', None)  
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for('login_client'))  

@app.route("/dashbordClient")
@login_required
def dashbordClient():
    if id:
        intervenants = Intervenant.query.all()
        clients = Client.query.all()
        interventions = Intervention.query.all()
        return render_template('dashbordClient.html', intervenants=intervenants, clients=clients,interventions=interventions)


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
    date_str = request.form['date']
    motive = request.form['motive']
    intervenant_id = request.form['intervenant_id']
    client_id = session.get('client_id') 
    intervenant = Intervenant.query.filter_by(id=intervenant_id).first()
    type_intervention= intervenant.poste
    try:
        date = datetime.fromisoformat(date_str)  
    except ValueError:
        flash("Format de date invalide. Veuillez entrer une date correcte.", "danger")
        return redirect(url_for('accueil_client', id=client_id))

    if client_id is None:
        flash("Client non connecté. Veuillez vous connecter pour créer une intervention.", "danger")
        return redirect(url_for('login_client'))

    new_intervention = Intervention(
        date=date,
        type=type_intervention,
        motive=motive,
        etat='en attente', 
        id_intervenant=intervenant_id,
        id_client=client_id
    )

    db.session.add(new_intervention)
    db.session.commit()
    flash("Intervention créée avec succès!", "success")

    return redirect(url_for('accueil_client', id=client_id))  


@app.route('/update_intervention_state/<int:id>', methods=['POST'])
@login_required
def update_intervention_state(id):
    intervention = Intervention.query.get_or_404(id)
    new_state = request.form['etat']
    
    intervention.etat = new_state
    db.session.commit()
    
    flash("État de l'intervention mis à jour avec succès!", "success")
    return redirect(url_for('dashbordIntervation'))  

@app.route('/graphe')
@login_required
def graphe():
    interventions = Intervention.query.all()
    intervenants = Intervenant.query.all()
    clients = Client.query.all()
    # 1. Calcul du nombre d'interventions réalisées et en attente
    total_interventions = Intervention.query.all()
    interventions_realisees = sum(1 for i in total_interventions if i.etat == 'réalisée')
    interventions_en_attente = len(total_interventions) - interventions_realisees

    # 2. Création du premier graphique (Tâches réalisées vs En attente)
    labels_1 = ['réalisées', 'attente']
    sizes_1 = [interventions_realisees, interventions_en_attente]
    colors_1 = ['#4CAF50', '#FF9800']
    explode_1 = (0.1, 0)

    fig1, ax1 = plt.subplots(figsize=(6, 6))
    ax1.pie(sizes_1, explode=explode_1, labels=labels_1, colors=colors_1, autopct='%1.1f%%', shadow=True, startangle=140)
    ax1.axis('equal') 

    # Enregistrer le graphique dans un objet BytesIO
    img1 = BytesIO()
    FigureCanvas(fig1).print_png(img1)
    img1.seek(0)
    img_b64_1 = base64.b64encode(img1.getvalue()).decode()

    # 3. Calcul des interventions réalisées par chaque intervenant
    interventions = Intervention.query.all()
    intervenants = Intervenant.query.all()

    # Créer un dictionnaire avec le nombre d'interventions par intervenant
    intervention_count = {intervenant.id: 0 for intervenant in intervenants}
    
    for intervention in interventions:
        if intervention.etat == 'réalisée':
            intervention_count[intervention.id_intervenant] += 1

    # Vérifier si certains intervenants ont des interventions à afficher
    if len(intervention_count) == 0 or sum(intervention_count.values()) == 0:
        # Si aucun intervenant n'a d'interventions, évitez l'erreur NaN
        labels_2 = ['Aucun intervenant']
        sizes_2 = [100]
    else:
        # Sinon, générez les données pour le graphique
        labels_2 = [f"{intervenant.nom} {intervenant.prenom}" for intervenant in intervenants]
        sizes_2 = [intervention_count[intervenant.id] for intervenant in intervenants]
    
    # 4. Création du deuxième graphique (Interventions réalisées par intervenant)
    fig2, ax2 = plt.subplots(figsize=(6, 6))
    ax2.pie(sizes_2, labels=labels_2, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
    ax2.axis('equal')  # Aspect égal pour que le graphique soit un cercle

    # Enregistrer le graphique dans un objet BytesIO
    img2 = BytesIO()
    FigureCanvas(fig2).print_png(img2)
    img2.seek(0)
    img_b64_2 = base64.b64encode(img2.getvalue()).decode()

    return render_template("graphe.html", graph_data_1=img_b64_1, graph_data_2=img_b64_2,interventions=interventions,intervenants=intervenants,clients=clients)




# ////////////////////////////////////////


@app.route("/accueil_intervenant/<int:id>")
def accueil_intervenant(id):
    intervenant = Intervenant.query.get_or_404(id)  # Récupérer l'intervenant par ID
    interventions = Intervention.query.filter_by(id_intervenant=id).all()  # Récupérer toutes les interventions de cet intervenant
    return render_template("accueil_intervenant.html", intervenant=intervenant, interventions=interventions)






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
        db.create_all()  
    app.run(debug=True)
