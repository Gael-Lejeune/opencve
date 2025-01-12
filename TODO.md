# TODO

## Français

- **Pensez à vérifier les TODO présents dans le code (avec grep ou une extension d'IDE)**

- Ajouter un outil pour faciliter à l'utilisateur l'ajout des Tag dans les fichiers excels permettant l'import du matériel des categories ?
  - Le faire via une API ? Ou toute autre solution permettant d'automatiser la génération de la colonne Tag dans Excel

- Ajout de suivi du traitement des cve par la category :
  - Pour commencer, une case à cocher par l'utilisateur pour dire qu'il a fait remonter la CVE au client ?

- Implémenter l'envoie d'email via un compte Microsoft live dédié.
  - Personnalisation des mail (envoi + ou - régulier en fonction de la criticité ? NB: Une gestion de seuil de criticité pour l'envoie des mails est déjà implémentée)

- Possibilité de rentrer les informations de calcul de criticité en fonction des information environnement de la category

- Regarder régulièrement les ajouts sur le github de OpenCVE [ici](https://github.com/opencve/opencve).

- Améliorer l'API

- Doc
  - Documentation de l'API
  - Documentation de l'utilisation de l'application
    - Comment update les elements suivis ?

- Vérifier si tout les produits cités sont bien vulnérables ([Github Issue](https://github.com/opencve/opencve/issues/184))

- Valider les tests du workflow en ligne ([ici](https://github.com/Gael-Lejeune/opencve/actions/workflows/tests.yml))
---
## English

- **Remember to check the TODOs present in the code (with grep or an IDE extension)**

- Add an extension to make the user easier to add the Tag in the Excel files containing the category ?
  - Do it via an API ? Or any other solution to automate the generation of the Tag column in Excel

- Add a tracking of the processing of CVEs by category :
  - To start, a checkbox by the user to say that he has raised the CVE to the client ?

- Implement the sending of emails via a Microsoft Live dedicated account.
  - Customization of the emails (sending + or - regularly according to the severity ? NB: A management of the severity threshold for the sending of emails is already implemented)

- Possibility to enter the information of severity calculation according to the environment information of the category

- Look regularly the additions on the github of OpenCVE [here](https://github.com/opencve/opencve).

- Improve the API

- Doc
  - API documentation
  - Application documentation
  - How to update the elements followed ?

- Verify if all the products cited are vulnerable ([Github Issue](https://github.com/opencve/opencve/issues/184))

- Validate the workflow online ([here](https://github.com/Gael-Lejeune/opencve/actions/workflows/tests.yml))