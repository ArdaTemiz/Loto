# tests/test_app.py

import unittest
from app import app, get_db, get_cursor
import mysql.connector
import json
from bs4 import BeautifulSoup

class LotoAppTestCase(unittest.TestCase):
    def setUp(self):
        # Configuration de l'application pour le test
        app.config['TESTING'] = True
        app.config['DB_NAME'] = 'loto_test_db'  # Utiliser une base de données de test
        self.app = app.test_client()

        # Pousser le contexte d'application
        self.app_context = app.app_context()
        self.app_context.push()

        # Créer la base de données de test
        self.connection = mysql.connector.connect(
            host=app.config['DB_HOST'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD']
        )
        self.cursor = self.connection.cursor()
        self.cursor.execute('CREATE DATABASE IF NOT EXISTS loto_test_db')
        self.connection.commit()
        self.cursor.execute('USE loto_test_db')

        # Créer les tables nécessaires
        self.create_tables()

        # Nettoyer les tables
        self.cursor.execute("DELETE FROM players")
        self.cursor.execute("DELETE FROM prize")
        self.cursor.execute("DELETE FROM jackpot")
        self.cursor.execute("INSERT INTO prize (id, amount) VALUES (1, 3000000)")
        self.cursor.execute("INSERT INTO jackpot (id, winning_numbers, winning_stars) VALUES (1, '', '')")
        self.connection.commit()

    def tearDown(self):
        # Popper le contexte d'application
        self.app_context.pop()

        self.cursor.close()
        self.connection.close()
        # Optionnel : Supprimer la base de données de test
        # self.cursor.execute('DROP DATABASE loto_test_db')

    def create_tables(self):
        # Créer la table 'players'
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                chosen_numbers VARCHAR(255) NOT NULL,
                chosen_stars VARCHAR(255) NOT NULL,
                gains FLOAT DEFAULT 0.0,
                matching_numbers VARCHAR(255),
                matching_stars VARCHAR(255),
                proximity_numbers INT DEFAULT 0,
                proximity_stars INT DEFAULT 0
            )
        ''')
        # Créer la table 'prize'
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prize (
                id INT PRIMARY KEY,
                amount FLOAT
            )
        ''')
        # Créer la table 'jackpot'
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS jackpot (
                id INT PRIMARY KEY,
                winning_numbers VARCHAR(255),
                winning_stars VARCHAR(255)
            )
        ''')
        self.connection.commit()

    def extract_text(self, response):
        """Helper method to extract text from HTML response."""
        soup = BeautifulSoup(response.get_data(as_text=True), 'html.parser')
        return soup.get_text()

    def test_accueil_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        response_text = self.extract_text(response)
        self.assertIn("Tentez votre chance", response_text)

    def test_add_player_success(self):
        response = self.app.post('/add_player', data={
            'name': 'TestPlayer',
            'chosen_numbers': '1,2,3,4,5',
            'chosen_stars': '1,2'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_text = self.extract_text(response)
        self.assertIn("Le joueur 'TestPlayer' a été ajouté avec succès.", response_text)

    def test_add_player_duplicate_name(self):
        # Ajouter un joueur
        self.app.post('/add_player', data={
            'name': 'TestPlayer',
            'chosen_numbers': '1,2,3,4,5',
            'chosen_stars': '1,2'
        }, follow_redirects=True)
        # Tenter d’ajouter un joueur avec le même nom
        response = self.app.post('/add_player', data={
            'name': 'TestPlayer',
            'chosen_numbers': '6,7,8,9,10',
            'chosen_stars': '3,4'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_text = self.extract_text(response)
        self.assertIn("Un joueur avec le nom 'TestPlayer' existe déjà.", response_text)

    def test_add_player_invalid_numbers(self):
        response = self.app.post('/add_player', data={
            'name': 'InvalidNumbersPlayer',
            'chosen_numbers': '50,51,52,53,54',  # Numéros invalides
            'chosen_stars': '1,2'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_text = self.extract_text(response)
        self.assertIn("Les numéros doivent être entre 1 et 49.", response_text)

    def test_add_player_invalid_stars(self):
        response = self.app.post('/add_player', data={
            'name': 'InvalidStarsPlayer',
            'chosen_numbers': '1,2,3,4,5',
            'chosen_stars': '10,11'  # Étoiles invalides
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_text = self.extract_text(response)
        self.assertIn("Les étoiles doivent être entre 1 et 9.", response_text)

    def test_generate_jackpot(self):
        # Ajouter des joueurs
        self.app.post('/add_player', data={
            'name': 'Joueur1',
            'chosen_numbers': '10,20,30,40,49',
            'chosen_stars': '1,2'
        }, follow_redirects=True)
        self.app.post('/add_player', data={
            'name': 'Joueur2',
            'chosen_numbers': '5,15,25,35,45',
            'chosen_stars': '3,4'
        }, follow_redirects=True)
        
        # Générer le jackpot
        response = self.app.get('/generate_jackpot')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data['winning_numbers']), 5)
        self.assertEqual(len(data['winning_stars']), 2)

    def test_update_prize(self):
        with app.app_context():
            response = self.app.post('/update_prize', data=json.dumps({'prize': '5000000'}),
                                     content_type='application/json')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['prize'], '5000000')
            
            # Vérifier dans la base de données
            cursor = get_cursor()
            cursor.execute("SELECT amount FROM prize WHERE id = 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 5000000)

    def test_delete_players(self):
        # Ajouter un joueur
        self.app.post('/add_player', data={
            'name': 'TestPlayer',
            'chosen_numbers': '1,2,3,4,5',
            'chosen_stars': '1,2'
        }, follow_redirects=True)
        
        # Supprimer tous les joueurs
        response = self.app.post('/delete_players', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_text = self.extract_text(response)
        self.assertIn("Tous les joueurs ont été supprimés avec succès.", response_text)
        
        # Vérifier directement dans la base de données
        with app.app_context():
            cursor = get_cursor()
            cursor.execute("SELECT COUNT(*) FROM players")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 0)

    def test_generate_players(self):
        # Générer 5 joueurs
        response = self.app.post('/generate_players', data={
            'num_players': '5'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier directement dans la base de données
        with app.app_context():
            cursor = get_cursor()
            cursor.execute("SELECT COUNT(*) FROM players")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 5)
        
        # Vérifier le message de succès dans la réponse HTML
        response_text = self.extract_text(response)
        self.assertIn("5 joueurs ont été générés avec succès.", response_text)
        
        # Vérifier les joueurs via la route /all_players
        response = self.app.get('/all_players')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data), 5)

if __name__ == '__main__':
    unittest.main()
