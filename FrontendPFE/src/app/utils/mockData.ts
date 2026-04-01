export interface Ticket {
  id: string;
  ref: string;
  demandeur: string;
  equipe: string;
  role: string;
  environnements: string[];
  niveauAcces: 'Base' | 'Sensible' | 'Critique';
  statut: 'En attente' | 'Approuvé' | 'Rejeté' | 'Escaladé';
  date: string;
  dateCreation: Date;
  accesDemandeDetails: Array<{
    nom: string;
    niveau: 'Base' | 'Sensible' | 'Critique';
    environnement: string;
  }>;
  analyseIA: {
    niveauPredit: 'Base' | 'Sensible' | 'Critique';
    scoreConfiance: number;
    explication: string;
  };
  historique: Array<{
    date: Date;
    acteur: string;
    action: string;
    details: string;
  }>;
}

export interface Admin {
  id: string;
  nom: string;
  email: string;
  role: 'Admin' | 'Super Admin';
  statut: 'Actif' | 'Inactif';
  derniereConnexion: Date;
}

export interface AuditLog {
  id: string;
  date: Date;
  acteur: string;
  action: string;
  ticketRef: string;
  environnement: string;
  resultat: 'Succès' | 'Échec';
  details: object;
}

export interface DecisionIA {
  id: string;
  ticketRef: string;
  niveauPredit: 'Base' | 'Sensible' | 'Critique';
  niveauReel: 'Base' | 'Sensible' | 'Critique';
  scoreConfiance: number;
  anomalie: boolean;
  date: Date;
}

export const mockTickets: Ticket[] = [
  {
    id: '1',
    ref: 'TKT-2026-001',
    demandeur: 'Mohamed Ben Ali',
    equipe: 'Développement Digital',
    role: 'Développeur Backend',
    environnements: ['DEV', 'QA'],
    niveauAcces: 'Base',
    statut: 'En attente',
    date: '2026-02-26',
    dateCreation: new Date('2026-02-26T09:30:00'),
    accesDemandeDetails: [
      { nom: 'API Gateway', niveau: 'Base', environnement: 'DEV' },
      { nom: 'Base de données clients', niveau: 'Base', environnement: 'QA' }
    ],
    analyseIA: {
      niveauPredit: 'Base',
      scoreConfiance: 94,
      explication: 'Profil développeur junior, accès limités aux environnements de test uniquement'
    },
    historique: [
      {
        date: new Date('2026-02-26T09:30:00'),
        acteur: 'Système',
        action: 'Ticket créé',
        details: 'Demande initiale soumise'
      }
    ]
  },
  {
    id: '2',
    ref: 'TKT-2026-002',
    demandeur: 'Fatma Gharbi',
    equipe: 'Infrastructure',
    role: 'Admin Système Senior',
    environnements: ['PROD', 'PREPROD'],
    niveauAcces: 'Critique',
    statut: 'Escaladé',
    date: '2026-02-25',
    dateCreation: new Date('2026-02-25T14:15:00'),
    accesDemandeDetails: [
      { nom: 'Serveurs Production', niveau: 'Critique', environnement: 'PROD' },
      { nom: 'Firewall Config', niveau: 'Critique', environnement: 'PROD' },
      { nom: 'Base données Core Banking', niveau: 'Critique', environnement: 'PREPROD' }
    ],
    analyseIA: {
      niveauPredit: 'Critique',
      scoreConfiance: 88,
      explication: 'Profil senior avec historique fiable, mais accès production nécessite validation Super Admin'
    },
    historique: [
      {
        date: new Date('2026-02-25T14:15:00'),
        acteur: 'Système',
        action: 'Ticket créé',
        details: 'Demande initiale soumise'
      },
      {
        date: new Date('2026-02-26T08:20:00'),
        acteur: 'Admin-Karim',
        action: 'Escaladé',
        details: 'Escaladé vers Super Admin pour validation niveau Critique'
      }
    ]
  },
  {
    id: '3',
    ref: 'TKT-2026-003',
    demandeur: 'Sami Trabelsi',
    equipe: 'Data Analytics',
    role: 'Data Scientist',
    environnements: ['DEV', 'QA'],
    niveauAcces: 'Sensible',
    statut: 'Approuvé',
    date: '2026-02-26',
    dateCreation: new Date('2026-02-26T10:45:00'),
    accesDemandeDetails: [
      { nom: 'Data Warehouse', niveau: 'Sensible', environnement: 'DEV' },
      { nom: 'BI Tools', niveau: 'Sensible', environnement: 'QA' }
    ],
    analyseIA: {
      niveauPredit: 'Sensible',
      scoreConfiance: 96,
      explication: 'Accès cohérent avec le rôle, équipe validée, environnements non-production'
    },
    historique: [
      {
        date: new Date('2026-02-26T10:45:00'),
        acteur: 'Système',
        action: 'Ticket créé',
        details: 'Demande initiale soumise'
      },
      {
        date: new Date('2026-02-26T10:46:00'),
        acteur: 'AUTO',
        action: 'Approuvé automatiquement',
        details: 'Score IA >95%, validation automatique'
      }
    ]
  },
  {
    id: '4',
    ref: 'TKT-2026-004',
    demandeur: 'Nesrine Bouazizi',
    equipe: 'Support Client',
    role: 'Agent Support',
    environnements: ['PROD'],
    niveauAcces: 'Critique',
    statut: 'Rejeté',
    date: '2026-02-24',
    dateCreation: new Date('2026-02-24T16:30:00'),
    accesDemandeDetails: [
      { nom: 'Base de données Core Banking', niveau: 'Critique', environnement: 'PROD' }
    ],
    analyseIA: {
      niveauPredit: 'Base',
      scoreConfiance: 12,
      explication: 'Anomalie détectée : Rôle Support ne nécessite pas accès Critique à la base Core Banking'
    },
    historique: [
      {
        date: new Date('2026-02-24T16:30:00'),
        acteur: 'Système',
        action: 'Ticket créé',
        details: 'Demande initiale soumise'
      },
      {
        date: new Date('2026-02-24T16:35:00'),
        acteur: 'Admin-Leila',
        action: 'Rejeté',
        details: 'Accès non justifié pour le rôle. Anomalie IA confirmée.'
      }
    ]
  },
  {
    id: '5',
    ref: 'TKT-2026-005',
    demandeur: 'Yassine Oueslati',
    equipe: 'Sécurité',
    role: 'Security Engineer',
    environnements: ['PROD', 'PREPROD', 'QA'],
    niveauAcces: 'Sensible',
    statut: 'En attente',
    date: '2026-02-26',
    dateCreation: new Date('2026-02-26T11:20:00'),
    accesDemandeDetails: [
      { nom: 'Logs Sécurité', niveau: 'Sensible', environnement: 'PROD' },
      { nom: 'SIEM Dashboard', niveau: 'Sensible', environnement: 'PREPROD' },
      { nom: 'Vulnerability Scanner', niveau: 'Sensible', environnement: 'QA' }
    ],
    analyseIA: {
      niveauPredit: 'Sensible',
      scoreConfiance: 91,
      explication: 'Profil sécurité validé, accès cohérents avec les responsabilités'
    },
    historique: [
      {
        date: new Date('2026-02-26T11:20:00'),
        acteur: 'Système',
        action: 'Ticket créé',
        details: 'Demande initiale soumise'
      }
    ]
  }
];

export const mockAdmins: Admin[] = [
  {
    id: '1',
    nom: 'Karim Mansouri',
    email: 'karim.mansouri@biat.com.tn',
    role: 'Super Admin',
    statut: 'Actif',
    derniereConnexion: new Date('2026-02-26T08:15:00')
  },
  {
    id: '2',
    nom: 'Leila Ben Salem',
    email: 'leila.bensalem@biat.com.tn',
    role: 'Admin',
    statut: 'Actif',
    derniereConnexion: new Date('2026-02-26T09:30:00')
  },
  {
    id: '3',
    nom: 'Ahmed Jebali',
    email: 'ahmed.jebali@biat.com.tn',
    role: 'Admin',
    statut: 'Actif',
    derniereConnexion: new Date('2026-02-25T17:45:00')
  },
  {
    id: '4',
    nom: 'Salma Hamdi',
    email: 'salma.hamdi@biat.com.tn',
    role: 'Admin',
    statut: 'Inactif',
    derniereConnexion: new Date('2026-02-15T10:20:00')
  }
];

export const mockAuditLogs: AuditLog[] = [
  {
    id: '1',
    date: new Date('2026-02-26T10:46:00'),
    acteur: 'AUTO',
    action: 'Approbation automatique',
    ticketRef: 'TKT-2026-003',
    environnement: 'DEV, QA',
    resultat: 'Succès',
    details: { scoreIA: 96, niveau: 'Sensible', justification: 'Auto-approved based on high confidence score' }
  },
  {
    id: '2',
    date: new Date('2026-02-26T08:20:00'),
    acteur: 'Admin-Karim',
    action: 'Escalade',
    ticketRef: 'TKT-2026-002',
    environnement: 'PROD, PREPROD',
    resultat: 'Succès',
    details: { motif: 'Niveau Critique nécessite validation Super Admin', niveauCible: 'Super Admin' }
  },
  {
    id: '3',
    date: new Date('2026-02-24T16:35:00'),
    acteur: 'Admin-Leila',
    action: 'Rejet',
    ticketRef: 'TKT-2026-004',
    environnement: 'PROD',
    resultat: 'Succès',
    details: { motif: 'Accès non justifié pour le rôle Support Client', anomalieIA: true }
  },
  {
    id: '4',
    date: new Date('2026-02-25T14:15:00'),
    acteur: 'Système',
    action: 'Création ticket',
    ticketRef: 'TKT-2026-002',
    environnement: 'PROD, PREPROD',
    resultat: 'Succès',
    details: { demandeur: 'Fatma Gharbi', equipe: 'Infrastructure' }
  },
  {
    id: '5',
    date: new Date('2026-02-26T09:30:00'),
    acteur: 'Système',
    action: 'Création ticket',
    ticketRef: 'TKT-2026-001',
    environnement: 'DEV, QA',
    resultat: 'Succès',
    details: { demandeur: 'Mohamed Ben Ali', equipe: 'Développement Digital' }
  }
];

export const mockDecisionsIA: DecisionIA[] = [
  {
    id: '1',
    ticketRef: 'TKT-2026-003',
    niveauPredit: 'Sensible',
    niveauReel: 'Sensible',
    scoreConfiance: 96,
    anomalie: false,
    date: new Date('2026-02-26T10:45:00')
  },
  {
    id: '2',
    ticketRef: 'TKT-2026-004',
    niveauPredit: 'Base',
    niveauReel: 'Critique',
    scoreConfiance: 12,
    anomalie: true,
    date: new Date('2026-02-24T16:30:00')
  },
  {
    id: '3',
    ticketRef: 'TKT-2026-002',
    niveauPredit: 'Critique',
    niveauReel: 'Critique',
    scoreConfiance: 88,
    anomalie: false,
    date: new Date('2026-02-25T14:15:00')
  },
  {
    id: '4',
    ticketRef: 'TKT-2026-001',
    niveauPredit: 'Base',
    niveauReel: 'Base',
    scoreConfiance: 94,
    anomalie: false,
    date: new Date('2026-02-26T09:30:00')
  },
  {
    id: '5',
    ticketRef: 'TKT-2026-005',
    niveauPredit: 'Sensible',
    niveauReel: 'Sensible',
    scoreConfiance: 91,
    anomalie: false,
    date: new Date('2026-02-26T11:20:00')
  }
];

export const statsData = {
  ticketsEnAttente: 2,
  ticketsTraitesAujourdhui: 3,
  decisionsAutomatiquesIA: 1,
  anomaliesDetectees: 1
};

export const evolutionTickets = [
  { jour: '20 Fév', total: 12 },
  { jour: '21 Fév', total: 15 },
  { jour: '22 Fév', total: 10 },
  { jour: '23 Fév', total: 18 },
  { jour: '24 Fév', total: 14 },
  { jour: '25 Fév', total: 16 },
  { jour: '26 Fév', total: 5 }
];

export const repartitionNiveaux = [
  { name: 'Base', value: 40, color: '#10B981' },
  { name: 'Sensible', value: 45, color: '#F59E0B' },
  { name: 'Critique', value: 15, color: '#EF4444' }
];
