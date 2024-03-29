[![DeepSource](https://app.deepsource.com/gh/ItsKandar/botus.svg/?label=active+issues&show_trend=true&token=MRqVBh5J5gaqplv9nFCED3aP)](https://app.deepsource.com/gh/ItsKandar/motus/?ref=repository-badge)
[![DeepSource](https://app.deepsource.com/gh/ItsKandar/botus.svg/?label=resolved+issues&show_trend=true&token=MRqVBh5J5gaqplv9nFCED3aP)](https://app.deepsource.com/gh/ItsKandar/motus/?ref=repository-badge)

# Botus

Inspiré par le celebre jeu TV "Motus"

## Comment ajouter le bot ?

Pour inviter le bot [cliquez ici!](https://discord.com/api/oauth2/authorize?client_id=1086344574689095741&permissions=8&scope=bot%20applications.commands)

## Serveur support

Rejoignez le serveur Discord pour obtenir de l'aide, poser des questions ou proposer des améliorations : [https://discord.gg/4M6596sjZa](https://discord.gg/4M6596sjZa)

## Commandes disponibles

Voici la liste des commandes disponibles (**Attention, vous devez d'abord definir le channel avec `set`**):

Commandes admins :
- `set` : defini le channel dans lequels le bot sera utilisable
- `create` : crée un channel "botus"
- `quoifeur (on/off)` : active/desactive les reponses automatiques du bot quand quelqu'un dit "quoi" ou d'autres mots :)

Commandes utilisateurs :
- `invite` : Envoie le lien d'invitation du bot
- `ping` : Pong (affiche la latence)!
- `bobo` : Botus !
- `start` : Commence une nouvelle partie
- `fin` : Termine la partie en cours
- `mot` : Envoie le mot (Toujours caché)
- `stats` : Montre le nombre de victoires
- `classement` : Montre le classement des victoires
- `suggest` : Pour suggerer une modification ou un mot
- `bug` : Report un bug
- `support` : Envoie le lien vers le serveur support
- `help` : Affiche la liste des commandes disponibles

## Comment jouer ?

1. Utilisez `start` pour commencer une nouvelle partie
2. Le bot affichera un mot à deviner avec les lettres masquées
3. Proposez un mot directement dans le chat
4. Le bot va renvoyer votre mot avec en dessous des carrées rouge, jaune ou noir

**ROUGE** signifie que la lettre est correctement placé

**JAUNE** signifie que la lettre n'est pas correctement placé

**NOIR** siginifie que la lettre n'est pas dans le mot

5. Vous avez 6 essais, si vous trouvez le mot, le jeu se termine et vous gagnez. Sinon, continuez à proposer des mots jusqu'à ce que vous le trouviez ou que vous décidiez d'arrêter la partie en utilisant `fin`!

Amusez-vous bien et bonne chance !


===================== CHANGELOG 13/10/23 ===================== 

- Ajout du nombre de lettre dans la commande /mot
- Modification du nombre d'essai a 6 essais (anciennement 7)
- Ajout du mot "Alien" dans le dictionnaire
- Modification de la commande /suggest :
    Anciennement "Suggère un mot ou nouvelle fonctionnalité"
    Maintenant "Suggère une nouvelle fonctionnalité"