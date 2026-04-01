Sidebar Modifications:
Add a toggle button (hamburger icon or chevron) at the top of the sidebar to collapse/expand it.
When collapsed, sidebar width reduces to 60px with only icons visible (logo small at top, navigation icons below).
When expanded, full 280px with text labels.
Make this toggle persistent across pages (use local storage simulation in design).
Update all pages with sidebar to show both states as variants.

Profile Icon and Logout in Navbar:
In the topbar, replace the direct logout button with a profile avatar icon (circle with initials or photo placeholder).
On click, open a dropdown menu with two options:
"Voir Profil" (links to new Profile page)
"Déconnexion" (red text or icon).

Dropdown: White background with shadow, positioned right-aligned, with divider between options.

New Page: Voir Profil:
Create a new full page "Profil Admin" (add to sidebar navigation below Gestion Admins).
Header: "Mon Profil"
Sections in cards:
Infos personnelles: Nom, Prénom, Email, Rôle (Admin/Super Admin), Date de création, Dernière connexion.
Bouton "Modifier Infos" → opens modal with editable fields (Nom, Prénom, Email).
Section Sécurité: Bouton "Changer Mot de Passe" → modal with fields (Ancien MDP, Nouveau MDP, Confirmer MDP, with eye icons and strength indicator).
Historique: Timeline of last 5 logins/actions.

Footer with "Sauvegarder Changements" button.

Gestion Admins Popup Modifications:
For "Ajouter un Admin" button: Change to a modal overlay (not full black screen) – use 50% transparent background dim, modal centered white card (width 500px).
Modal content: Form fields (Nom, Prénom, Email, Rôle dropdown: Admin/Super Admin, Mot de passe temporaire generated or input).
Buttons: "Ajouter" (primary blue), "Annuler" (secondary).
Ensure the underlying dashboard page remains visible but dimmed behind the modal.

Modification Admin Popup:
In the admins table, add "Modifier" button per row (pencil icon).
On click: Open similar modal overlay (transparent dim, centered card) pre-filled with admin data.
Form: Same as add, plus current status toggle.
Buttons: "Sauvegarder" (blue), "Annuler".

Admin Status Logic in Gestion Admins:
In the admins table, for Status column: Badge green "Actif" or red "Inactif".
Next to it, conditional button:
If Actif: Red button "Désactiver" (with confirmation modal: "Êtes-vous sûr ?").
If Inactif: Green button "Activer".

Show variants in design for both states.

Supervision IA Page Enhancements (make it even more detailed like the second design prompt):
Add detailed "Règles d’Automatisation par Équipe" section: Matrix table with rows for teams (e.g., Middleware, Développement, Ops, Sécurité), columns for Rôles, Environnements, Accès par Défaut (badges list), and Actions (Modifier/Supprimer).
Expand graphs: Confusion matrix for IA predictions, Evolution précision over time, Feature importance bar chart.
Add "Éditer Règles IA" button → modal to adjust thresholds (e.g., confidence for auto-approve, anomaly alert level).
More anomalies section: Cards with "Demande inhabituelle" details, IA reasoning bullets, and "Ignorer/Valider" buttons.

Notifications in Accueil (and Global):
In topbar, next to profile icon, add bell icon for notifications.
On click: Open dropdown menu (white shadow card, right-aligned, width 350px).
Content: List of 5-10 sample notifications (e.g., "Nouveau ticket critique escaladé", "Anomalie IA détectée sur ticket REF-123", with timestamp, unread bold).
Header: "Notifications" + "Marquer tout lu".
Footer: "Voir toutes" link.
Show unread count badge on bell icon (red circle).