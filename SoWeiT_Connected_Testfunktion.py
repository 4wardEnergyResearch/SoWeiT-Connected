""""
Name:       Aufruf_Optimierer.py
Projekt:    SoWeiT Connected
Autor:      4ward Energy Research GmbH
Datum:      01.12.2021
Status:     final

Beschreibung:   Diese Funktion ruft den Optimierer auf und stellt eine Testumgebung zur Verfügung
            
"""

import numpy as np
import pandas as pd
import datetime as dt
from SoWeiT_Connected_Optimierer import Optimierer


#Definition der benötigten Variablen für die Testumgebung

#Simulationsdauer - in diesem Beispiel 2 Tage mit 15-Sekunden Messwerten
sim_dauer = 5760*2
#Variable zum Speichern der Verteilung der PV-Energie über das Direktleitungssystem - wird nur für die Testfunktion benötigt
res_opt = np.zeros([7,])
#Zähler für die über das Direktleitungssystem zugewissene PV-Energie (Gesamtwert)
pv_verbrauch_energie_stand = np.zeros([7,])
#Zähler für den Gesamtverbrauch der Nutzer
verbrauch_energie_stand = np.zeros([7,])
#Ergebnis des Optimierers (optimale Schaltzustände)
schaltzustaende = np.zeros((sim_dauer,7))
#Zeitstempel Startzeitpunkt der Simulation
zeitstempel = dt.datetime(2021,8,31,0,0,0)


#Testdaten einlesen (ggf. Pfad hinzufügen)
testdaten = pd.read_csv("Testdaten.csv",sep = ";")

#Testdaten in numpy Array umwandeln
verbrauch = testdaten[["V1","V2","V3","V4","V5","V6","V7"]].to_numpy()
erzeugung = testdaten[["PV"]].to_numpy()

#Initialisieren des Optimierers
Opt1 = Optimierer(7,5*60,60)

#Aufruf der "update_verteilung_mittels_energie"-Funktion
Opt1.update_verteilung_mittels_energie(pv_verbrauch_energie_stand, verbrauch_energie_stand)

#Aufruf der Optimierungsfunktion und speichern der Ergebnisse
for j in range(0,sim_dauer):
    
    #Zähler für die bereits optimierten Tage
    if j % 5760 == 0:
        print("Tag: "+str(j / 5760+1))
               
    #Update des Zeitstempels
    zeitstempel = zeitstempel + (dt.datetime(2021,8,10,0,0,15)-dt.datetime(2021,8,10,0,0,0))
   
    #Aufruf des Optimierers für jeden Zeitschritt
    schaltzustaende[j,:], res_opt = Opt1.run(erzeugung[j,0],verbrauch[j,:],zeitstempel)
    
    #Berechnen der neuen Energiestände
    pv_verbrauch_energie_stand = pv_verbrauch_energie_stand+res_opt
    verbrauch_energie_stand = verbrauch_energie_stand +verbrauch[j,:]
    
    #Update der Verteilung - muss nicht in jedem Zeitschritt erfolgen
    Opt1.update_verteilung_mittels_energie(pv_verbrauch_energie_stand, verbrauch_energie_stand)
    

