""""
Name:       Direktleitungsmodell_Optimierer.py
Projekt:    SoWeiT Connected
Autor:      4ward Energy Research GmbH
Datum:      01.12.2021
Status:     final

Beschreibung: Optimierungsfunktion für das SoWeiT Connected Direktleitungssystem (DLS) - 
              entspricht jener Funktion, die auf dem EOS-Energy Manager läuft.
"""

import logging

_logger = logging.getLogger(__name__)

import numpy as np
from pyomo.environ import AbstractModel, Set, Param
from pyomo.environ import Var, Boolean, NonNegativeReals
from pyomo.environ import Constraint, maximize, Objective, SolverFactory, value


class Optimierer:
    def __init__(self, N, sperrzeit_1, sperrzeit_2):
        #Anzahl der Nutzer
        self.N = N
        #Sperrzeit in Sekunden
            #Sperrzeit_1: Zeit während der nur bei positivem Schaltkontingent geschalten werden darf
            #Sperrzeit_2: Zeit während der auch bei positivem Schaltkontingent nicht geschalten werden darf
        self.sperrzeit_1 = sperrzeit_1
        self.sperrzeit_2 = sperrzeit_2
        #Erzeugung der PV-Anlage
        self.erzeugung = np.zeros(N)
        #Gewichtungsfaktor zur Verbesserung der Gleichverteilung (faire Verteilung des PV-Überschusses über das DLS zwischen den Nutzern)
        self.faktor = np.zeros(N)
        #Variable zum Speicher der Energieverbräuche und der bereits zugewiesenen Energie über das DLS
        self.verteilung = np.zeros([N, 2])
        #Schaltkontingent zur Bestimmung der Sperrzeit
        self.schaltkontingent = np.zeros(N)
        #Variable zum Speichern des letzten Schaltvorgangs
        self.schaltzeit = np.zeros((N), dtype='datetime64[s]')
        
        #self.schaltfreigabe = np.zeros(N)
        
        #Aktueller Schaltzustand (Direktleitung oder öffentliches Netz)
        self.schaltzustand = np.zeros([N, 2])
        #Zähler für die über das DLS zugewissene PV-Energie (Gesamtwert)
        self.pv_verbrauch_energie_stand = None
        #Zähler für den Gesamtverbrauch der Nutzer
        self.verbrauch_energie_stand = None
        
    #Funktion zum Aufbereiten der Daten für den Solver
    def prepare_data(self, verbrauch):
        N = len(verbrauch)
        nutzer_labels = ["N" + str(i) for i in range(1, N + 1)]
        verbraucher_table = {nutzer_labels[i]: verbrauch[i] for i in range(0, N)}
        data = {None: {'nutzer': {None: nutzer_labels},
                       'verbrauch': verbraucher_table}}
        return data

    # 1. Nebenbedingung (Summe, der über das DLS zugewiesenen Energie muss kleiner als die gesamte PV-Erzeugung sein)
    def summe_direkt(self, m):
        return sum(m.nutzerdirekt[n] for n in m.nutzer) <= self.erzeugung

    # 2. Nebenbedingung (jeder Nutzer muss entweder über das DLS oder über das öffentliche Netz versorgt werden, eine teilweise Versorgung über das DLS ist nicht zulässig)
    def verbraucher(self, m, n):
        return m.nutzerdirekt[n] == m.einaus[n] * m.verbrauch[n]

    # Zielfunktion
    def zielfkt(self, m):

        return sum(m.nutzerdirekt[n] for n in m.nutzer) \
               + sum(m.nutzerdirekt["N" + str(i + 1)] * self.faktor[i] for i in range(0, self.N)) * 100
    
    # Pre-processing um häufiges Takten zu vermeiden - Einführen eines Schaltkontingents
    def preprocessing(self,zeitstempel,verbrauch):
        
        N = len(verbrauch)
        schaltfreigabe = np.zeros(N)
        
        #Erhöhen des Schaltkontingents pro Aufruf
            #Das Schaltkontingent wurde so ausgelegt, dass die max. Schaltvorgänge innerhalb von 15 Jahren nicht überschritten werden (Lebensdauer der Komponenten)
        self.schaltkontingent[:] = self.schaltkontingent[:] + 0.032
        #Speichern des letzten Schaltzustands (1.Spalte: Schaltzustand von t-1, 2.Spalte: Schaltzustand von t)
        self.schaltzustand[:,0] = self.schaltzustand[:,1]

        #Berechnen der Schaltfreigabe (1: Optimierer darf Nutzer x einschalten, 0: Optimerer darf Nutzer x nicht einschalten)
        for j in range(np.size(self.schaltkontingent,0)):
            
            #Die Schaltfreigabe erfolgt wenn...
            #der Nutzer bereits im letzten Zeitschritt vom DLS versorgt wurde            
            if self.schaltzustand[j,0] == 1:
                schaltfreigabe[j] = 1  
            #die 1. Sperrzeit abgelaufen ist
            elif (np.datetime64(zeitstempel)-self.schaltzeit[j]).astype('timedelta64[s]').astype(np.int32) >= self.sperrzeit_1:
                schaltfreigabe[j] = 1 
            #das Schaltkontingent positiv ist und die 2. Sperrzeit abgelaufen ist
            elif self.schaltkontingent[j] >= 1 and ((np.datetime64(zeitstempel)-self.schaltzeit[j]).astype('timedelta64[s]').astype(np.int32) >= self.sperrzeit_2):
                schaltfreigabe[j] = 1 
            else:
                schaltfreigabe[j] = 0
       
        #Ist die Schaltfreigabe negativ wird der Verbrauch fiktiv auf 0 gesetzt
        verbrauch = verbrauch * schaltfreigabe
            
        return verbrauch
       
    #Post-processing um häufiges Takten zu vermeiden
    def postprocessing(self,zeitstempel):
        
        #Update des Schaltkontingents, wenn eine Schaltung (Ein- oder Ausschalten) erfolgt ist
        for j in range(np.size(self.schaltkontingent,0)):
            
            #Einschalten: Reduktion des Schaltkontingents
            if self.schaltzustand[j,1] == 1 and self.schaltzustand[j,0] == 0:
                self.schaltkontingent[j] = self.schaltkontingent[j] - 1
            #Ausschalten: Reduktion des Schaltkontingents und Speichern des Ausschaltzeitpunkts zur Einhaltung der Sperrzeit
            elif self.schaltzustand[j,1] == 0 and self.schaltzustand[j,0] == 1:
                self.schaltzeit[j] = zeitstempel
                self.schaltkontingent[j] = self.schaltkontingent[j] - 1
                      

    # Optimierer
    def run(self, erzeugung_in, verbrauch, zeitstempel):
        
        #Bestimmen der Anzahl der Nutzer
        N = len(verbrauch)
        self.erzeugung = erzeugung_in
        
        #Aufruf Pre-processing
        verbrauch = self.preprocessing(zeitstempel,verbrauch)

        # Definieren der Rückgabewerte
        res_opt = np.zeros(N)

        # Definieren des Optimierungsmodells
        m = AbstractModel()

        # Definieren der verwendeten Sets
        m.nutzer = Set()

        # Parameter
        m.verbrauch = Param(m.nutzer)

        # Variablen
        m.nutzerdirekt = Var(m.nutzer, domain=NonNegativeReals)
        m.einaus = Var(m.nutzer, domain=Boolean)

        # Constraints
        m.c_verbraucher = Constraint(m.nutzer, rule=self.verbraucher)
        m.c_summe_direkt = Constraint(rule=self.summe_direkt)

        # Zielfunktion
        m.o_zielfkt = Objective(rule=self.zielfkt, sense=maximize)

        # Daten für Solver
        data = self.prepare_data(verbrauch)
        _logger.debug(f"{data=}")

        # Aufruf Solver
        _logger.debug("Aufruf Solver")
        try:
            instance = m.create_instance(data=data)
            opt = SolverFactory('cbc')
            opt.solve(instance)
            # Speichern der Ergebnisse sowie der Gesamtenergiemengen
            for i in range(0, N):
                res_opt[i] = value(instance.nutzerdirekt['N' + str(i + 1)])
        except Exception as e:
            _logger.exception(e)
        _logger.debug("Aufruf Solver done")

        #Bestimmen der Schaltzustände
        for j in range(np.size(self.schaltkontingent,0)):
            
            if res_opt[j] > 0:
                self.schaltzustand[j,1] = 1
            else:
                self.schaltzustand[j,1] = 0

        #Aufruf Post-processing
        self.postprocessing(zeitstempel)
        
        #Rückgabewerte (res_opt wird nur für die Testfunktion benötigt)
        return self.schaltzustand[:,1], res_opt

    #Funktion zum Updaten der Energiemengen mittels Zählerständen
        #pv_verbrauch_energie_stand: Gesamte über das DLS zugewiesene Energie pro Nutzer
        #verbrauch_energie_stand: Gesamte bisher verbrauchte Energie pro Nutzer
    def update_verteilung_mittels_energie(self, pv_verbrauch_energie_stand, verbrauch_energie_stand):
        if self.pv_verbrauch_energie_stand is not None and self.verbrauch_energie_stand is not None:
            pv_verbrauch_deltas = pv_verbrauch_energie_stand - self.pv_verbrauch_energie_stand
            verbrauch_deltas = verbrauch_energie_stand - self.verbrauch_energie_stand
            self.update_verteilung(pv_verbrauch_deltas, verbrauch_deltas)

        self.pv_verbrauch_energie_stand = pv_verbrauch_energie_stand
        self.verbrauch_energie_stand = verbrauch_energie_stand
        
    #Funktion zum Updaten der Energiemengen mittels Differenzwerten
    def update_verteilung(self, pv_verbrauch_deltas, verbrauch_deltas):
        _logger.debug(f"update_verteilung({pv_verbrauch_deltas=}, {verbrauch_deltas=}):")
        self.verteilung[:, 0] = self.verteilung[:, 0] + pv_verbrauch_deltas
        self.verteilung[:, 1] = self.verteilung[:, 1] + verbrauch_deltas
        self._update_faktor()

    #Funktion zum Updaten des Priorisierungsfaktors zur Verbesserung der Gleichverteilung
    def _update_faktor(self):
        # Berechnen des Anteils der über das DLS zugewissenen Energiemenge bezogen auf den Gesamtverbrauch des jeweiligen Nutzers
        with np.errstate(divide='ignore', invalid='ignore'):
            p_verteilung = self.verteilung[:, 0] / self.verteilung[:, 1]
        # Berechnen des Verteilungsfaktor zur Verbesserung der Gleichverteilung
        faktorwert = 0.7
        for i in range(0, self.N):
            index = np.argmax(p_verteilung)
            self.faktor[index] = faktorwert

            p_verteilung[index] = -1
            faktorwert = faktorwert + 0.1
        _logger.debug(f"update faktor {self.faktor=}")