document.addEventListener('DOMContentLoaded', function() {
    const chosenNumbers = [];
    const chosenStars = [];
    const chosenNumbersInput = document.getElementById('chosen_numbers');
    const chosenStarsInput = document.getElementById('chosen_stars');

    // Créer des éléments de message pour les grilles
    const numbersMessage = document.createElement('p');
    const starsMessage = document.createElement('p');

    numbersMessage.style.color = 'red';
    starsMessage.style.color = 'red';

    numbersMessage.style.display = 'none';
    starsMessage.style.display = 'none';

    document.getElementById('numbers-grid').after(numbersMessage);
    document.getElementById('stars-grid').after(starsMessage);

    // Fonction pour générer la grille de numéros (1 à 49)
    window.generateNumberGrid = function() {
        const numbersGrid = document.getElementById('numbers-grid');
        numbersGrid.innerHTML = ''; // Effacer toute grille précédente

        for (let i = 1; i <= 49; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            btn.classList.add('number-btn');
            btn.style.width = "50px";
            btn.style.height = "50px";
            btn.style.borderRadius = "50%";
            btn.style.backgroundColor = "grey";
            btn.style.color = "white";
            btn.style.border = "none";
            btn.style.margin = "5px";
            btn.style.cursor = "pointer";
            btn.style.fontSize = "18px";
            btn.style.display = "inline-flex";
            btn.style.justifyContent = "center";
            btn.style.alignItems = "center";

            btn.onclick = function(event) {
                event.preventDefault();
                if (chosenNumbers.includes(i)) {
                    const index = chosenNumbers.indexOf(i);
                    chosenNumbers.splice(index, 1); // Supprimer le numéro de la sélection
                    btn.style.backgroundColor = "grey";
                    numbersMessage.style.display = 'none'; // Masquer le message
                } else if (chosenNumbers.length < 5) {
                    chosenNumbers.push(i); // Ajouter le numéro à la sélection
                    btn.style.backgroundColor = "red";
                    if (chosenNumbers.length === 5) {
                        numbersMessage.textContent = "Nombre maximal de numéros atteint !";
                        numbersMessage.style.display = 'block'; // Afficher le message
                    }
                }
                chosenNumbersInput.value = chosenNumbers.join(',');
                toggleNumberButtons();
            };
            numbersGrid.appendChild(btn);
        }
    };

    // Fonction pour générer la grille d'étoiles (1 à 9)
    window.generateStarGrid = function() {
        const starsGrid = document.getElementById('stars-grid');
        starsGrid.innerHTML = ''; // Effacer toute grille précédente

        for (let i = 1; i <= 9; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            btn.classList.add('star-btn');
            btn.style.width = "50px";
            btn.style.height = "50px";
            btn.style.borderRadius = "50%";
            btn.style.backgroundColor = "orange";
            btn.style.color = "black";
            btn.style.border = "none";
            btn.style.margin = "5px";
            btn.style.cursor = "pointer";
            btn.style.fontSize = "18px";

            btn.onclick = function(event) {
                event.preventDefault();
                if (chosenStars.includes(i)) {
                    const index = chosenStars.indexOf(i);
                    chosenStars.splice(index, 1); // Supprimer l'étoile de la sélection
                    btn.style.backgroundColor = "orange";
                    starsMessage.style.display = 'none'; // Masquer le message
                } else if (chosenStars.length < 2) {
                    chosenStars.push(i); // Ajouter l'étoile à la sélection
                    btn.style.backgroundColor = "red";
                    if (chosenStars.length === 2) {
                        starsMessage.textContent = "Nombre maximal d'étoiles atteint !";
                        starsMessage.style.display = 'block'; // Afficher le message
                    }
                }
                chosenStarsInput.value = chosenStars.join(',');
                toggleStarButtons();
            };
            starsGrid.appendChild(btn);
        }
    };

    // Fonction pour activer/désactiver les boutons de numéros
    function toggleNumberButtons() {
        const buttons = document.querySelectorAll('.number-btn');
        buttons.forEach(btn => {
            const number = parseInt(btn.textContent);
            if (chosenNumbers.length >= 5 && !chosenNumbers.includes(number)) {
                btn.disabled = true; // Désactiver les boutons non sélectionnés
            } else {
                btn.disabled = false; // Activer les boutons sélectionnés ou si moins de 5 numéros
            }
        });
    }

    // Fonction pour activer/désactiver les boutons d'étoiles
    function toggleStarButtons() {
        const buttons = document.querySelectorAll('.star-btn');
        buttons.forEach(btn => {
            const star = parseInt(btn.textContent);
            if (chosenStars.length >= 2 && !chosenStars.includes(star)) {
                btn.disabled = true; // Désactiver les boutons non sélectionnés
            } else {
                btn.disabled = false; // Activer les boutons sélectionnés ou si moins de 2 étoiles
            }
        });
    }

    // Générer une grille aléatoire pour les numéros et étoiles
    document.getElementById('generate-random').onclick = function(event) {
        event.preventDefault();

        // Réinitialiser les sélections actuelles
        chosenNumbers.length = 0;
        chosenStars.length = 0;
        numbersMessage.style.display = 'none'; // Masquer le message
        starsMessage.style.display = 'none'; // Masquer le message
        document.querySelectorAll('.number-btn').forEach(btn => {
            btn.classList.remove('selected');
            btn.style.backgroundColor = "grey";
            btn.disabled = false; // Réactiver tous les boutons de numéros
        });
        document.querySelectorAll('.star-btn').forEach(btn => {
            btn.classList.remove('selected');
            btn.style.backgroundColor = "orange";
            btn.disabled = false; // Réactiver tous les boutons d'étoiles
        });

        // Générer 5 numéros uniques aléatoires de 1 à 49
        const randomNumbers = generateRandomNumbers(5, 1, 49);
        randomNumbers.forEach(num => {
            chosenNumbers.push(num);
            document.querySelector(`.number-btn:nth-child(${num})`).classList.add('selected');
            document.querySelector(`.number-btn:nth-child(${num})`).style.backgroundColor = "red";
        });

        // Générer 2 étoiles uniques aléatoires de 1 à 9
        const randomStars = generateRandomNumbers(2, 1, 9);
        randomStars.forEach(star => {
            chosenStars.push(star);
            document.querySelector(`.star-btn:nth-child(${star})`).classList.add('selected');
            document.querySelector(`.star-btn:nth-child(${star})`).style.backgroundColor = "red";
        });

        // Mettre à jour les inputs cachés
        chosenNumbersInput.value = chosenNumbers.join(',');
        chosenStarsInput.value = chosenStars.join(',');

        // Afficher les messages si des limites sont atteintes
        if (chosenNumbers.length === 5) {
            numbersMessage.textContent = "Nombre maximal de numéros atteint !";
            numbersMessage.style.display = 'block'; // Afficher le message
        }
        if (chosenStars.length === 2) {
            starsMessage.textContent = "Nombre maximal d'étoiles atteint !";
            starsMessage.style.display = 'block'; // Afficher le message
        }

        // Désactiver les autres boutons après la génération
        toggleNumberButtons();
        toggleStarButtons();
    };

    // Générer des nombres uniques aléatoires dans une plage donnée
    function generateRandomNumbers(count, min, max) {
        const numbers = new Set();
        while (numbers.size < count) {
            const randomNumber = Math.floor(Math.random() * (max - min + 1)) + min;
            numbers.add(randomNumber);
        }
        return Array.from(numbers);
    }

    // Suppression des joueurs
    document.getElementById('delete-players-form').onsubmit = function(event) {
        event.preventDefault(); // Empêcher le rechargement de la page

        fetch('/delete_players', {
            method: 'POST',
        })
        .then(response => response.text())
        .then(html => {
            document.body.innerHTML = html;
            // Après suppression, regénérer les grilles
            generateNumberGrid();
            generateStarGrid();
        })
        .catch(error => console.error('Erreur lors de la suppression des joueurs :', error));
    };

    // Appeler les fonctions pour générer les grilles au chargement initial
    generateNumberGrid();
    generateStarGrid();
});
