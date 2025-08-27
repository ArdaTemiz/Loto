from flask import Flask, render_template, request, redirect, url_for, jsonify, g
import mysql.connector
import random
import re

app = Flask(__name__)

# Configuration par défaut de la base de données
app.config['DB_HOST'] = 'localhost'
app.config['DB_USER'] = 'root'
app.config['DB_PASSWORD'] = ''
app.config['DB_NAME'] = 'loto_db'

# Charger une configuration spécifique si nécessaire
app.config.from_pyfile('config.py', silent=True)

# Fonction pour obtenir la connexion à la base de données
def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=app.config['DB_HOST'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'],
            database=app.config['DB_NAME']
        )
    return g.db

# Fonction pour obtenir un curseur
def get_cursor():
    return get_db().cursor(buffered=True)

# Fermer la connexion à la base de données à la fin de chaque requête
@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Définir les pourcentages de gain
GAIN_PERCENTAGES = [40, 20, 12, 7, 6, 5, 4, 3, 2, 1]  # Pour les 10 premiers

# Page d'accueil
@app.route('/')
def accueil():
    return render_template('accueil.html')

# Page des règles
@app.route('/regles')
def regles():
    return render_template('regles.html')

# Page de tirage
@app.route('/index')
def index():
    cursor = get_cursor()
    # Vérifier le nombre total de joueurs
    cursor.execute("SELECT COUNT(*) FROM players")
    total_players = cursor.fetchone()[0]

    # Calculer combien de places restent avant d'atteindre 100, minimum à 0
    remaining_slots = max(0, 100 - total_players)

    return render_template('index.html', total_players=total_players, remaining_slots=remaining_slots)

# Page de classement
@app.route('/classement')
def classement():
    cursor = get_cursor()
    query = "SELECT amount FROM prize LIMIT 1"
    cursor.execute(query)
    result = cursor.fetchone()
    prize_amount = result[0] if result else 3000000  # Si non défini, valeur par défaut

    # Récupérer la liste des joueurs
    cursor.execute("SELECT * FROM players")
    players = cursor.fetchall()

    # Vérifier s'il y a des joueurs
    total_players = len(players)

    # Passer la liste des joueurs et le total au template
    return render_template('classement.html', prize=prize_amount, players=players, total_players=total_players)

# Route pour ajouter un joueur dans la base de données
@app.route('/add_player', methods=['POST'])
def add_player():
    name = request.form['name']
    chosen_numbers = request.form['chosen_numbers']
    chosen_stars = request.form['chosen_stars']

    # Expression régulière pour n'autoriser que les lettres et les espaces
    if not re.match(r'^[A-Za-zÀ-ÖØ-öø-ÿ\s]+$', name):
        return render_template('index.html', error_message="Le nom doit contenir uniquement des lettres.", remaining_slots=get_remaining_slots())

    # Validation des numéros et étoiles choisis
    try:
        chosen_numbers_list = [int(n) for n in chosen_numbers.split(',') if n]
        chosen_stars_list = [int(s) for s in chosen_stars.split(',') if s]
    except ValueError:
        return render_template('index.html', error_message="Veuillez entrer des numéros valides.", remaining_slots=get_remaining_slots())

    if len(chosen_numbers_list) != 5 or len(chosen_stars_list) != 2:
        return render_template('index.html', error_message="Vous devez choisir exactement 5 numéros et 2 étoiles.", remaining_slots=get_remaining_slots())

    if not all(1 <= n <= 49 for n in chosen_numbers_list):
        return render_template('index.html', error_message="Les numéros doivent être entre 1 et 49.", remaining_slots=get_remaining_slots())

    if not all(1 <= s <= 9 for s in chosen_stars_list):
        return render_template('index.html', error_message="Les étoiles doivent être entre 1 et 9.", remaining_slots=get_remaining_slots())

    if len(set(chosen_numbers_list)) != 5:
        return render_template('index.html', error_message="Les numéros doivent être uniques.", remaining_slots=get_remaining_slots())

    if len(set(chosen_stars_list)) != 2:
        return render_template('index.html', error_message="Les étoiles doivent être uniques.", remaining_slots=get_remaining_slots())

    cursor = get_cursor()

    # Vérifier si un joueur avec ce nom existe déjà
    cursor.execute("SELECT * FROM players WHERE name = %s", (name,))
    existing_player = cursor.fetchone()

    if existing_player:
        return render_template('index.html', error_message=f"Un joueur avec le nom '{name}' existe déjà.", remaining_slots=get_remaining_slots())

    # Vérifier le nombre total de joueurs dans la base de données
    cursor.execute("SELECT COUNT(*) FROM players")
    total_players = cursor.fetchone()[0]

    # Limite de 100 participants
    if total_players >= 100:
        return render_template('index.html', error_message="Le nombre maximum de 100 participants a été atteint.", remaining_slots=get_remaining_slots())

    gains = 0.00

    # Requête SQL pour insérer le joueur dans la base de données
    query = "INSERT INTO players (name, chosen_numbers, chosen_stars, gains) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (name, chosen_numbers, chosen_stars, gains))
    get_db().commit()

    # Recalculer le nombre de places restantes
    remaining_slots = get_remaining_slots()

    return render_template('index.html', success_message=f"Le joueur '{name}' a été ajouté avec succès.", remaining_slots=remaining_slots)


def get_remaining_slots():
    cursor = get_cursor()
    cursor.execute("SELECT COUNT(*) FROM players")
    total_players = cursor.fetchone()[0]
    remaining_slots = max(0, 100 - total_players)
    return remaining_slots


# Route pour récupérer le classement
@app.route('/ranking', methods=['GET'])
def get_ranking():
    cursor = get_cursor()
    query = """
        SELECT 
            name, 
            chosen_numbers, 
            chosen_stars, 
            gains, 
            IFNULL(matching_numbers, ''), 
            IFNULL(matching_stars, ''), 
            IFNULL(proximity_numbers, 0), 
            IFNULL(proximity_stars, 0) 
        FROM players 
        ORDER BY gains DESC, proximity_numbers ASC, proximity_stars ASC
    """
    cursor.execute(query)
    results = cursor.fetchall()

    ranking = []
    for row in results:
        chosen_numbers = [int(num) for num in row[1].split(',') if num]
        chosen_stars = [int(star) for star in row[2].split(',') if star]
        matching_numbers = [int(num) for num in row[4].split(',') if num]
        matching_stars = [int(star) for star in row[5].split(',') if star]

        ranking.append({
            'name': row[0],
            'chosen_numbers': chosen_numbers,
            'chosen_stars': chosen_stars,
            'gains': float(row[3]),
            'matching_numbers': matching_numbers,
            'matching_stars': matching_stars,
            'proximity_numbers': int(row[6]),
            'proximity_stars': int(row[7])
        })

    # Limiter à 10 joueurs pour le classement
    ranking = ranking[:10]

    return jsonify(ranking)

# Route pour récupérer tous les joueurs (sans limite)
@app.route('/all_players', methods=['GET'])
def get_all_players():
    cursor = get_cursor()
    # Utilisation de CAST pour extraire le numéro dans le nom
    query = """
        SELECT name, chosen_numbers, chosen_stars 
        FROM players 
        ORDER BY CAST(SUBSTRING(name, 8) AS UNSIGNED) ASC
    """
    cursor.execute(query)
    results = cursor.fetchall()

    players = []
    for row in results:
        players.append({
            'name': row[0],
            'chosen_numbers': list(map(int, row[1].split(','))),
            'chosen_stars': list(map(int, row[2].split(',')))
        })

    return jsonify(players)

# Route pour générer aléatoirement des joueurs avec des numéros et étoiles
@app.route('/generate_players', methods=['POST'])
def generate_players():
    num_players = int(request.form['num_players'])

    cursor = get_cursor()

    # Vérifier le nombre total de joueurs actuels
    cursor.execute("SELECT COUNT(*) FROM players")
    total_players = cursor.fetchone()[0]

    # Calculer combien de joueurs peuvent encore être ajoutés
    remaining_slots = max(0, 100 - total_players)

    # Si aucune place disponible, afficher un message d'erreur
    if remaining_slots == 0:
        return render_template(
            'index.html',
            error_message="Le nombre maximum de participants est atteint. Il n'y a plus de places disponibles.",
            remaining_slots=remaining_slots
        )

    # Si le nombre de joueurs à ajouter dépasse les places restantes, afficher un message d'erreur
    if num_players > remaining_slots:
        return render_template(
            'index.html',
            error_message=f"Vous essayez d'ajouter {num_players} joueurs, mais il ne reste que {remaining_slots} places disponibles.",
            remaining_slots=remaining_slots
        )

    # Ajouter les joueurs si toutes les conditions sont satisfaites
    for i in range(1, num_players + 1):
        player_num = total_players + i
        name = f"Joueur_{player_num}"
        chosen_numbers_list = random.sample(range(1, 50), 5)
        chosen_numbers = ",".join(map(str, chosen_numbers_list))
        chosen_stars_list = random.sample(range(1, 10), 2)
        chosen_stars = ",".join(map(str, chosen_stars_list))
        gains = 0.00

        query = "INSERT INTO players (name, chosen_numbers, chosen_stars, gains) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, chosen_numbers, chosen_stars, gains))

    get_db().commit()

    # Recalculer après l'ajout
    cursor.execute("SELECT COUNT(*) FROM players")
    total_players = cursor.fetchone()[0]
    remaining_slots = max(0, 100 - total_players)

    # Créer le message de succès
    success_message = f"{num_players} joueurs ont été générés avec succès."

    return render_template(
        'index.html',
        success_message=success_message,
        remaining_slots=remaining_slots
    )

# Route pour supprimer tous les joueurs
@app.route('/delete_players', methods=['POST'])
def delete_players():
    cursor = get_cursor()
    # Suppression de tous les joueurs
    cursor.execute("DELETE FROM players")
    get_db().commit()

    # Recalculer le nombre de places restantes (ici 100 après suppression)
    remaining_slots = 100  # Après suppression, il reste 100 places

    # Rendre la page index avec les grilles réinitialisées
    return render_template('index.html', success_message="Tous les joueurs ont été supprimés avec succès.", remaining_slots=remaining_slots)

# Route pour modifier la cagnotte
@app.route('/update_prize', methods=['POST'])
def update_prize():
    try:
        new_prize = request.json.get('prize')

        # Validation pour s'assurer que le nouveau montant est un nombre valide
        if not new_prize or not new_prize.isdigit():
            return jsonify({'error_message': 'Montant invalide'}), 400

        cursor = get_cursor()
        # Vérification et mise à jour de la cagnotte dans la base de données
        query = "UPDATE prize SET amount = %s WHERE id = 1"
        cursor.execute(query, (new_prize,))
        get_db().commit()

        # Retourner la nouvelle cagnotte et un message de succès
        return jsonify({'prize': new_prize, 'success_message': 'Cagnotte modifiée avec succès'}), 200
    except Exception as e:
        return jsonify({'error_message': f'Erreur lors de la mise à jour de la cagnotte: {str(e)}'}), 500

# Fonction pour obtenir le montant total de la cagnotte
def get_total_prize():
    cursor = get_cursor()
    cursor.execute("SELECT amount FROM prize LIMIT 1")
    result = cursor.fetchone()
    return result[0] if result else 3000000  # Par défaut 3 000 000 si non défini

# Fonction pour vérifier si deux joueurs sont égaux selon les critères
def are_players_equal(player1, player2):
    return (
        len(player1['matching_numbers']) == len(player2['matching_numbers']) and
        len(player1['matching_stars']) == len(player2['matching_stars']) and
        player1['proximity_numbers'] == player2['proximity_numbers'] and
        player1['proximity_stars'] == player2['proximity_stars']
    )

# Fonction pour distribuer les gains en respectant les règles
def distribute_gains(players):
    total_prize = get_total_prize()  # Obtenir la cagnotte actuelle
    gain_percentages = GAIN_PERCENTAGES.copy()  # Liste des pourcentages à distribuer
    num_players = len(players)

    # Si moins de 10 participants, redistribuer les pourcentages non attribués
    if num_players < 10:
        allocated_percentages = gain_percentages[:num_players]
        total_allocated = sum(allocated_percentages)  # Pourcentage total alloué aux joueurs
        total_percentage = sum(gain_percentages)  # Total des pourcentages disponibles
        missing_percentage = total_percentage - total_allocated  # Pourcentage non alloué

        # Redistribuer le pourcentage non alloué parmi les joueurs existants
        for i in range(num_players):
            gain_percentages[i] += (gain_percentages[i] / total_allocated) * missing_percentage

    i = 0
    rank = 1
    while i < len(players) and rank <= 10:
        tie_players = [players[i]]
        j = i + 1
        while j < len(players) and are_players_equal(players[i], players[j]):
            tie_players.append(players[j])
            j += 1

        # Calculer le gain partagé
        percentage_sum = sum(gain_percentages[rank - 1:rank - 1 + len(tie_players)])
        shared_gain = (total_prize * percentage_sum) / (100 * len(tie_players))
        shared_gain = round(shared_gain, 2)

        for player in tie_players:
            player['gains'] = shared_gain

        i = j
        rank += len(tie_players)

    # Les joueurs au-delà du 10ème n'obtiennent rien
    for player in players[10:]:
        player['gains'] = 0.00

    return players

# Route pour générer le jackpot et le stocker dans la base de données
@app.route('/generate_jackpot', methods=['GET'])
def generate_jackpot():
    cursor = get_cursor()
    # Générer les numéros gagnants
    winning_numbers = random.sample(range(1, 50), 5)
    winning_stars = random.sample(range(1, 10), 2)

    # Mettre à jour le jackpot dans la base de données
    query = "UPDATE jackpot SET winning_numbers = %s, winning_stars = %s WHERE id = 1"
    cursor.execute(query, (",".join(map(str, winning_numbers)), ",".join(map(str, winning_stars))))
    get_db().commit()

    # Comparer les résultats des joueurs avec le jackpot
    players = compareResultsWithJackpot(winning_numbers, winning_stars)
    players_with_gains = distribute_gains(players)

    # Mettre à jour les gains des joueurs
    for player in players_with_gains:
        cursor.execute("""
            UPDATE players SET gains = %s, matching_numbers = %s, matching_stars = %s, proximity_numbers = %s, proximity_stars = %s WHERE name = %s
        """, (
            player['gains'],
            ",".join(map(str, player['matching_numbers'])),
            ",".join(map(str, player['matching_stars'])),
            player['proximity_numbers'],
            player['proximity_stars'],
            player['name']
        ))
    get_db().commit()

    return jsonify({
        'winning_numbers': winning_numbers,
        'winning_stars': winning_stars
    })

# Fonction pour comparer les résultats des joueurs avec le jackpot
def compareResultsWithJackpot(winning_numbers, winning_stars):
    cursor = get_cursor()
    cursor.execute("SELECT name, chosen_numbers, chosen_stars FROM players")
    results = cursor.fetchall()

    players = []

    for row in results:
        player_name = row[0]
        chosen_numbers = list(map(int, row[1].split(',')))
        chosen_stars = list(map(int, row[2].split(',')))

        # Correspondances exactes
        matching_numbers = [num for num in chosen_numbers if num in winning_numbers]
        matching_stars = [star for star in chosen_stars if star in winning_stars]

        # Numéros restants après correspondance
        remaining_winning_numbers = [num for num in winning_numbers if num not in matching_numbers]
        remaining_player_numbers = [num for num in chosen_numbers if num not in matching_numbers]

        remaining_winning_stars = [star for star in winning_stars if star not in matching_stars]
        remaining_player_stars = [star for star in chosen_stars if star not in matching_stars]

        # Calcul de la proximité des numéros
        proximity_numbers = 0
        temp_player_numbers = remaining_player_numbers.copy()
        for win_num in remaining_winning_numbers:
            if not temp_player_numbers:
                proximity_numbers += 49  # Valeur maximale
                continue
            closest_num = min(temp_player_numbers, key=lambda x: abs(win_num - x))
            proximity_numbers += abs(win_num - closest_num)
            temp_player_numbers.remove(closest_num)

        # Calcul de la proximité des étoiles
        proximity_stars = 0
        temp_player_stars = remaining_player_stars.copy()
        for win_star in remaining_winning_stars:
            if not temp_player_stars:
                proximity_stars += 9  # Valeur maximale
                continue
            closest_star = min(temp_player_stars, key=lambda x: abs(win_star - x))
            proximity_stars += abs(win_star - closest_star)
            temp_player_stars.remove(closest_star)

        # Somme des numéros pour départager
        sum_winning_numbers = sum(winning_numbers)
        sum_player_numbers = sum(chosen_numbers)
        sum_proximity = abs(sum_winning_numbers - sum_player_numbers)

        players.append({
            'name': player_name,
            'chosen_numbers': chosen_numbers,
            'chosen_stars': chosen_stars,
            'matching_numbers': matching_numbers,
            'matching_stars': matching_stars,
            'proximity_numbers': proximity_numbers,
            'proximity_stars': proximity_stars,
            'sum_proximity': sum_proximity,
            'gains': 0.00,
        })

    # Déterminer si des correspondances existent
    any_matches = any(
        len(player['matching_numbers']) > 0 or len(player['matching_stars']) > 0
        for player in players
    )

    if not any_matches:
        # Trier par somme de proximité
        players.sort(key=lambda x: x['sum_proximity'])
    else:
        # Trier selon les critères définis
        players.sort(key=lambda x: (
            -len(x['matching_numbers']),
            -len(x['matching_stars']),
            x['proximity_numbers'],
            x['proximity_stars']
        ))

    return players

if __name__ == '__main__':
    app.run(debug=True)
