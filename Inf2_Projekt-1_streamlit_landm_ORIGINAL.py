# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 14:18:30 2023

@author: marcl
"""

# Imports
import streamlit as st
import pandas as pd
import datetime
import json
import matplotlib.pyplot as plt
import numpy as np 
import graphviz
from jsonbin import load_data_jsonbin, save_data_jsonbin, load_key, save_key
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import textwrap

#Laden der Daten

# -------- load secrets for jsonbin.io --------
jsonbin_secrets_Referenzwerte_Hersteller = st.secrets["jsonbin_Referenzwerte_Hersteller"]
jsonbin_secrets_DB1 = st.secrets["jsonbin_DB1"]

# Funktion zum Laden des Datensatzes der eingegebenen Parameter aus einer JSON-Datei von jsonbin
def load_data():
    return load_data_jsonbin(jsonbin_secrets_DB1["api_key"], jsonbin_secrets_DB1["bin_id_DB1"])

# Funktion zum Speichern des Datensatzes der eingegebenen Parameter in einer JSON-Datei von jsonbin
def save_data(data):
    return save_data_jsonbin(jsonbin_secrets_DB1["api_key"], jsonbin_secrets_DB1["bin_id_DB1"], data)
        
# Funktion zum Laden der Referenzwerte gemäss Hersteller aus einer JSON-Datei von jsonbin
def load_data_ref_para():
    return load_data_jsonbin(jsonbin_secrets_Referenzwerte_Hersteller["api_key"], jsonbin_secrets_Referenzwerte_Hersteller["bin_id_Referenzwerte_Hersteller"])
       
# Laden der JSON-Daten
json1 = load_data()

# JSON in Dataframe umwandeln
df1=pd.DataFrame(json1)

# -------- user login --------
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

fullname, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == True:   # login successful
    authenticator.logout('Logout', 'main')   # show logout button
elif authentication_status == False:
    st.error('Username/password is incorrect')
    st.stop()
elif authentication_status == None:
    st.warning('Please enter your username and password')
    st.stop()

# Löschen des letzten Eintrages    
def delete_last():
    # delete last entry
    data_to_delete = load_data()
    data_to_delete.pop()
    res = save_data(data_to_delete)
    if 'message' in res:
        st.error(res['message'])
        
# Suchen von Daten via Datum/Zeit Spalte und Anzeige dieser Daten (mit input6 Feld)
def search_and_display_row(df, column_name):
    value = input6
    matching_rows = df[df[column_name].str.contains(value)]
    if len(value) == 0:
        st.text("Geben Sie Suchparameter ein")
    elif not matching_rows.empty:
        st.text("Gefundene Parameter:")
        st.dataframe(matching_rows)
    else:
        st.text("Keine Parameter entsprechen den Suchparametern!")

# Löschen der gefundenen Daten        
def delete_all_searched_rows(df, column_name):
    value = input6
    matching_rows = df[df[column_name].str.contains(value)]
    
    if delete_button == True and len(value) == 0 or matching_rows.empty:
        st.warning("Keine Parameter entsprechen den Suchparametern!")
        return df 

    if delete_button == True and len(value) > 0: 
        df = df.drop(matching_rows.index)
        st.success("Zeilen erfolgreich gelöscht.")
        st.dataframe(df.tail())
        return df


# Funktionen für Statistik

def sbereich(dataframe, Spalte_Resultate , mittelwert, standardabweichung):
    ''' berechnet die s-Bereiche mit den angegebenen Mittelwert und Standardabweichung.
    danach wird die Berechnung in der dataframe als neue Spalte hinzugefügt.'''
    
    #verwandet Werte in der kat in numerische Typ.
    dataframe[Spalte_Resultate] = pd.to_numeric(dataframe[Spalte_Resultate], errors='coerce')
    
    # berechnet für jede Reihe die s-Bereich bzw. die Standardberechnung
    dataframe["s-Bereich"] = (dataframe[Spalte_Resultate] - mittelwert) / standardabweichung
    
    # schränkt die Bereich in -3 bis 3 ein.
    dataframe["s-Bereich"] = np.clip(dataframe["s-Bereich"], a_min=-3, a_max=3)
    
    return dataframe

def leveyjennings(df, datum):
    # create a color list for the scatter plot dots
    colors = ['red' if y >= 3 or y <= -3 else 'yellow' if 2 <= y < 3 or -3 < y <= -2 else 'green' for y in df['s-Bereich']]
    
    # Scatterplot 
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df[datum], df['s-Bereich'], c=colors)
    ax.set_xlabel('Datum')
    ax.set_ylim(-3.05, 3.05)
    ax.set_ylabel('s-Bereich')
    ax.set_title('Levey Jennings Kurve')
    
    # rotate x-axis labels
    plt.xticks(rotation=45)
    return st.pyplot(fig)

def sortieren_nach_Datum_neuste(dataframe,Spalte_Datum_Jahr):
    #sotiert nach Datum und gibt den letzen Jahren heraus. df= Dataframe, Year= Spalte mit Datum/Jahr.
    return dataframe.sort_values(Spalte_Datum_Jahr,ascending=False).head(10)

def Beurteilung_Westgard_Regel(dataframe, Spalte_Datum, Spalte_s_Bereich):
    ''' Beurteilung mittels Westgard Regel für Qualitätskontrollen. Quelle: https://www.qualab.swiss/Aktuelle-Richtlinien.htm , https://www.westgard.com/mltirule.htm. 
    dataframe=dataframe, Spalte_Datum=Spalte mit Datum und Zeit, Spalte_s_Bereich= Spalte mit s-Bereich
    filtriert die letzten zwei Werten'''
    
    last_2 = dataframe.sort_values(Spalte_Datum, ascending=False).head(2)
    
    # letzte_Wert = letzte Wert und zweit_letzte_Wert = zweit letzte Wert
    letzte_Wert = last_2.head(1)
    letzte_Wert= float(letzte_Wert[Spalte_s_Bereich])
    zweit_letzte_Wert = last_2.sort_values(Spalte_Datum, ascending=True).head(1)
    zweit_letzte_Wert=float(zweit_letzte_Wert[Spalte_s_Bereich])
    
    #Mit if-Statements die Qualitätskontrolle kontrollieren.
    if abs(letzte_Wert) >= 2.0 and abs(letzte_Wert) < 3.0:
        
    # Wenn der letzte Wert zwischen Kontroll- und Warngrenze ist können im "Subheader" vorkommende Westgard-Regel verletzt werden. Damit die s-Bereich in Minus Bereich einbezogen wird, wird der Betrag je nach Wert 
        if letzte_Wert > 0 and zweit_letzte_Wert < 0 and letzte_Wert + abs(zweit_letzte_Wert) >= 4.0 and zweit_letzte_Wert >= 2.0 and zweit_letzte_Wert <= 3:
            return st.subheader(""":red[R4s Regel verletzt]""")
        elif letzte_Wert < 0 and zweit_letzte_Wert > 0 and abs(letzte_Wert) + zweit_letzte_Wert >= 4.0 and zweit_letzte_Wert >= 2.0 and zweit_letzte_Wert <= 3:
            return st.subheader(""":red[R4s Regel verletzt]""")
        elif abs(zweit_letzte_Wert) >= 2.0:
            return st.subheader(""":red[2-2s Regel wurde verletzt.]""")      
        else:
              return st.subheader(""":orange[1-2s Regel wurde verletzt. Wenn nächste Messung wieder in 2s-Bereich ist, wird die 2-2s Regel verletzt.]""")
 
    elif abs(letzte_Wert) == 3.0:
    # Wenn der Wert 3 mal vom Standardabweichung abweicht. 
        return st.subheader(""":red[1-3s Regel verletzt.]""")

    elif letzte_Wert > 0 and zweit_letzte_Wert < 0 and letzte_Wert + abs(zweit_letzte_Wert) >= 4.0:
    #Für den R4s Verletzung
        return st.subheader(""":red[4s Regel verletzt]""")

    elif letzte_Wert < 0 and zweit_letzte_Wert > 0 and abs(letzte_Wert) + zweit_letzte_Wert >= 4.0:
    #Für den R4s Verletzung
        return st.subheader(""":red[R4s Regel verletzt]""")

    else:
    #Wenn der Wert kein Westgard-Regel verletzt.
        return st.subheader(""":green[Sie dürfen arbeiten.]""")
    
def df_nach_Parameter_aussortiert_fuer_Status(Parameter_option):
    if len(Parameter_option) > 0:
        
        # Button zum Parameter selektieren.
        df_nach_Parameter_aussortiert=df1[df1["Parameter (Gerät)"]==Parameter_option]
        
        # Damit die s-Bereichen berechnet werden kann müssen die Hersteller angegebenen Mittelwerten und Standabweichung aus dem json file geholt werden.
        Hersteller_Angaben= load_data_ref_para()
        
        
        # Aussortieren
        #'Hersteller_Angaben' ist eine Liste von Dictionaries
        Hersteller_Angaben = pd.DataFrame(Hersteller_Angaben)  
        
        # Convert list of dictionaries to DataFrame
        Hersteller_Angaben["Datum/Zeit"] = pd.to_datetime(Hersteller_Angaben["Datum/Zeit"])  # Convert datetime column to datetime format

        # Werte Sortieren 
        df_nach_Parameter_aussortiert=df1[df1["Parameter (Gerät)"] == Parameter_option]
        
    if "Parameter (Gerät)" in Hersteller_Angaben.columns:
        Hersteller_Angaben_filtriert = Hersteller_Angaben[Hersteller_Angaben["Parameter (Gerät)"] == Parameter_option]
        
        # Filter Werten Parameter_option filtern
        Hersteller_Angaben_filtriert = Hersteller_Angaben_filtriert.sort_values("Datum/Zeit", ascending=False).head(1)                  
       
        # Im Dataframe neue Spalte herstellen, um beim jeden Wert den Standardabweichung auszurechnen.
        df_nach_Parameter_aussortiert = sbereich(df_nach_Parameter_aussortiert,"Wert",float(Hersteller_Angaben_filtriert["Mittelwert"]),float(Hersteller_Angaben_filtriert["Standardabweichung"]))
       
        # Die 10 neusten Werten sortieren und nach aufsteigende Datum sortieren.
        df_nach_Parameter_aussortiert_Status = sortieren_nach_Datum_neuste(df_nach_Parameter_aussortiert, "Datum/Zeit").sort_values("Datum/Zeit",ascending=True)
       
        #hilft bei der Beurteilung.
    return df_nach_Parameter_aussortiert_Status    
    
def Beurteilung_Status(dataframe, Spalte_Datum, Spalte_s_Bereich):
    ''' Beurteilung mittels Westgard Regel für Qualitätskontrollen. Quelle: https://www.qualab.swiss/Aktuelle-Richtlinien.htm , https://www.westgard.com/mltirule.htm. 
    dataframe=dataframe, Spalte_Datum=Spalte mit Datum und Zeit, Spalte_s_Bereich= Spalte mit s-Bereich
    filtriert die letzten zwei Werten'''
    
    last_2 = dataframe.sort_values(Spalte_Datum, ascending=False).head(2)
    
    # letzte_Wert = letze Wert und zweit_letzte_Wert = zweit letzte Wert
    letzte_Wert = last_2.head(1)
    letzte_Wert= float(letzte_Wert[Spalte_s_Bereich])
    zweit_letzte_Wert = last_2.sort_values(Spalte_Datum, ascending=True).head(1)
    zweit_letzte_Wert=float(zweit_letzte_Wert[Spalte_s_Bereich])
    
    #Mit if-Statements die Qualitätskontrolle kontrollieren.
    if abs(letzte_Wert) >= 2.0 and abs(letzte_Wert) < 3.0:

        # Wenn der letzte Wert zwischen Kontroll- und Warngrenze ist können im "Subheader" vorkommende Westgard-Regel verletzt werden. Damit die s-Bereich in Minus Bereich einbezogen wird, wird der Betrag je nach Wert 
        if letzte_Wert > 0 and zweit_letzte_Wert < 0 and letzte_Wert + abs(zweit_letzte_Wert) >= 4.0 and zweit_letzte_Wert >= 2.0 and zweit_letzte_Wert <= 3:
            return st.error(""":red[R4s Regel verletzt]""")
        elif letzte_Wert < 0 and zweit_letzte_Wert > 0 and abs(letzte_Wert) + zweit_letzte_Wert >= 4.0 and zweit_letzte_Wert >= 2.0 and zweit_letzte_Wert <= 3:
            return st.error(""":red[R4s Regel verletzt]""")
        elif abs(zweit_letzte_Wert) >= 2.0:
            return st.error(""":red[2-2s Regel wurde verletzt.]""")      
        else:
              return st.warning(""":yellow[1-2s Regel wurde verletzt. Wenn nächste Messung wieder in 2s-Bereich ist, wird die 2-2s Regel verletzt.]""")
    
    elif abs(letzte_Wert) == 3.0:
    # Wenn der Wert 3 mal vom Standardabweichung abweicht. 
        return st.error(""":red[1-3s Regel verletzt.]""")
    
    elif letzte_Wert > 0 and zweit_letzte_Wert < 0 and letzte_Wert + abs(zweit_letzte_Wert) >= 4.0:
    #Für den R4s Verletzung
        return st.error(""":red[4s Regel verletzt]""")
    
    elif letzte_Wert < 0 and zweit_letzte_Wert > 0 and abs(letzte_Wert) + zweit_letzte_Wert >= 4.0:
    #Für den R4s Verletzung
        return st.error(""":red[R4s Regel verletzt]""")
   
    else:
    #Wenn der Wert kein Westgard-Regel verletzt.
        return st.success(""":green[Sie dürfen arbeiten.]""")

###################################################################################################################################################################################################################

##### Website/App Darstellung #####


# Tabs Controller
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Home", "Status", "Input", "Werte", "Gesamt-System", "Anleitung"])


### Home Tab
with tab1:
    st.title("Qualitätskontrolle Sysmex")
    st.image("https://www.mittelstandsbund.de/fileadmin/_processed_/d/d/csm_visuelle_qualitaetskontrolle_2_9541de070d.png")
    st.caption("Bild Quelle:")
    st.caption("https://www.mittelstandsbund.de/fileadmin/_processed_/d/d/csm_visuelle_qualitaetskontrolle_2_9541de070d.png")

### Status Tab
with tab2:
    st.title("Status")
    
    
    # Anzeige der entsprechenden Stati zu den jeweiligen Parametern
    
    st.subheader("Leukozyten (Sysmex)")
    df_sortiert_nach_Status=df_nach_Parameter_aussortiert_fuer_Status('Leukozyten (Sysmex)')
    Beurteilung_Status(df_sortiert_nach_Status,"Datum/Zeit","s-Bereich")
    
    st.subheader("Neutrophile (Sysmex)")
    df_sortiert_nach_Status=df_nach_Parameter_aussortiert_fuer_Status('Neutrophile (Sysmex)')
    Beurteilung_Status(df_sortiert_nach_Status,"Datum/Zeit","s-Bereich")
    
    st.subheader("Lymphozyten (Sysmex)")
    df_sortiert_nach_Status=df_nach_Parameter_aussortiert_fuer_Status('Lymphozyten (Sysmex)')
    Beurteilung_Status(df_sortiert_nach_Status,"Datum/Zeit","s-Bereich")
    
    st.subheader("Monozyten (Sysmex)")
    df_sortiert_nach_Status=df_nach_Parameter_aussortiert_fuer_Status('Monozyten (Sysmex)')
    Beurteilung_Status(df_sortiert_nach_Status,"Datum/Zeit","s-Bereich")
    
    st.subheader("Eosinophile (Sysmex)")
    df_sortiert_nach_Status=df_nach_Parameter_aussortiert_fuer_Status('Eosinophile (Sysmex)')
    Beurteilung_Status(df_sortiert_nach_Status,"Datum/Zeit","s-Bereich")
    
    st.subheader("Basophile (Sysmex)")
    df_sortiert_nach_Status=df_nach_Parameter_aussortiert_fuer_Status('Basophile (Sysmex)')
    Beurteilung_Status(df_sortiert_nach_Status,"Datum/Zeit","s-Bereich")
    
    

### Input Tab
with tab3:
    st.title("Input")

    #Inputs zum Ausfüllen     
    input1 = st.selectbox('Parameterauswahl:',('Dropdown','Leukozyten (Sysmex)','Neutrophile (Sysmex)','Lymphozyten (Sysmex)','Monozyten (Sysmex)','Eosinophile (Sysmex)','Basophile (Sysmex)'))
    input2 = st.text_input('Parameterwert in [Anzahl/ul] eingeben:')
    input3 = st.text_input('Lotnummer:')
    input4 = st.text_input('Kommentar:')
    st.write('')
    st.write('Visum (automatisch ausgefüllt):')
    st.write(username)
    input5 = username
    st.write('')
        
    # Button um Werte in JSON-Datei einzufügen           
    if st.button('Werte eingeben'):
        
        # Überprüfung der Eingabewerte und anfügen in JSON-Datei, wenn Kriterien erfüllt
        if input1!='Dropdown' and input2.isdigit() and len(input2)>0 and len(input5)>0 and input3.isdigit() and len(input3)>0:
           new_row_in_json1 = {
               'Datum/Zeit': datetime.datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S"),
               'Parameter (Gerät)': input1,
               'Wert': input2,
               'Einheit': 'Anzahl/ul',
               'Lotnummer': input3,
               'Visum': input5,
               'Kommentar': input4
               }
       
           json1.append(new_row_in_json1)
           save_data(json1)
           st.text('Daten wurden hochgeladen')
           st.write('')
           
        # Wenn die Kriterien nicht erfüllt sind geschied bei jedem definietem Fall folgendes
        elif input2.isdigit()==False:
            if len(input2)==0:
                st.error("Error: Nicht alle benötigten Daten sind ausgefüllt!", icon="⚠️")
            else:
                st.error("Error: Parameterwert-Eingabe ist keine Zahl! Nur Zahlenwert eingeben.", icon="🚨")
        elif input3.isdigit()==False:
            if len(input3)==0:
                st.error("Error: Nicht alle benötigten Daten sind ausgefüllt!", icon="⚠️")
            else:
                st.error("Error: Lotnummer-Eingabe ist keine Zahl!", icon="🚨")        
        else:
            st.error("Error: Nicht alle benötigten Daten sind ausgefüllt!", icon="⚠️")

    st.write('')        
    st.header("Falscher letzter Eintrag löschen") 
    
    st.text('Letzter Eintrag:')
    json1_letzte_eingegebenen_Daten_alles = load_data()
    df_letzte_eingegebenen_Daten_sortiert = pd.DataFrame(json1_letzte_eingegebenen_Daten_alles).tail(1)
    st.dataframe(df_letzte_eingegebenen_Daten_sortiert)
        
    if st.button('Letzter Eintrag löschen'):
        delete_last()
    
    
### Werte Tab
with tab4:
    #JSON in Dataframe umwandeln
    df_Werten=pd.DataFrame(json1)
    st.title("Werte")
    
    Parameter_option = st.selectbox(
    'Welche Parameter möchten Sie als Levey Jennings Kurve ansehen?',
    ('Leukozyten (Sysmex)','Neutrophile (Sysmex)','Lymphozyten (Sysmex)','Monozyten (Sysmex)','Eosinophile (Sysmex)','Basophile (Sysmex)'))
       
    if len(Parameter_option) > 0:
        # Button zum Parameter selektieren.
        df_nach_Parameter_aussortiert=df_Werten[df_Werten["Parameter (Gerät)"]==Parameter_option]
        
        # Dataframe generieren.
        st.dataframe(df_nach_Parameter_aussortiert[::-1])
        
        # Damit die s-Bereichen berechnet werden kann müssen die Hersteller angegebenen Mittelwerten und Standabweichung aus dem json file geholt werden.
        Hersteller_Angaben= load_data_ref_para()
        
        
        # Aussortieren
        #'Hersteller_Angaben' ist eine Liste von Dictionaries
        Hersteller_Angaben = pd.DataFrame(Hersteller_Angaben)  
        
        # Convert list of dictionaries to DataFrame
        Hersteller_Angaben["Datum/Zeit"] = pd.to_datetime(Hersteller_Angaben["Datum/Zeit"])  # Convert datetime column to datetime format

        # Werte Sortieren 
        df_nach_Parameter_aussortiert=df_Werten[df_Werten["Parameter (Gerät)"] == Parameter_option]
        
        # Extrahieren der letzten 10 Zeilen aus dem DataFrame
        last_10 = df_nach_Parameter_aussortiert["Wert"].tail(10)
      
        # Berechnen
        mean_last_10 = last_10.astype(int).mean()
      
        # Ergebnis
        st.write("Mittelwert der letzten 10 Werte:")
        st.write(mean_last_10)
        
        
        # Im Dataframe neue Spalte herstellen, um beim jeden Wert den Standardabweichung auszurechnen.
        
    if "Parameter (Gerät)" in Hersteller_Angaben.columns:
        Hersteller_Angaben_filtriert = Hersteller_Angaben[Hersteller_Angaben["Parameter (Gerät)"] == Parameter_option]
        
        # Filter Werten Parameter_option filtern
        Hersteller_Angaben_filtriert = Hersteller_Angaben_filtriert.sort_values("Datum/Zeit", ascending=False).head(1)    
              
        # Im Dataframe neue Spalte herstellen, um beim jeden Wert den Standardabweichung auszurechnen.
        df_nach_Parameter_aussortiert = sbereich(df_nach_Parameter_aussortiert,"Wert",float(Hersteller_Angaben_filtriert["Mittelwert"]),float(Hersteller_Angaben_filtriert["Standardabweichung"]))
       
        # Die 10 neusten Werten sortieren und nach aufsteigende Datum sortieren.
        df_nach_Parameter_aussortiert_nach_Datum_sortiert = sortieren_nach_Datum_neuste(df_nach_Parameter_aussortiert, "Datum/Zeit").sort_values("Datum/Zeit",ascending=True)
        
        # Die Levey Jennings Kurve erstellen. Die Werten, die über 3 Standardabweichungen sind rot.
        leveyjennings(df_nach_Parameter_aussortiert_nach_Datum_sortiert,"Datum/Zeit")
       
        # hilft bei der Beurteilung.
        Beurteilung_Westgard_Regel(df_nach_Parameter_aussortiert,"Datum/Zeit","s-Bereich")
        
        
### Gesamt-System Tab
with tab5:
    
    with st.expander('Suche Parameter mit Datum/Zeit'):
        # Laden der JSON-Daten
        json1 = load_data()
        # JSON in Dataframe umwandeln
        df1=pd.DataFrame(json1)
    
        input6 = st.text_input('Suche Parameter via Datum/Zeit')
        search_and_display_row(df1, 'Datum/Zeit')
        delete_button = st.button('Gefundene Daten löschen')
        
        if delete_button:
            df1 = delete_all_searched_rows(df1, 'Datum/Zeit')
            df1.to_json('json1.json')
            save_data(json1)
    
    
    # Laden der JSON-Daten
    json1 = load_data()

    # JSON in Dataframe umwandeln
    df1=pd.DataFrame(json1)
    
    st.title("Gesamt-System")
    st.dataframe(df1[::-1])
    
### Anleitung Tab
with tab6:
    st.title("Anleitung")
    with st.expander("Werte eingeben"):
        st.header("Werte eingeben")
        st.write('Um Ihre Werte einzugeben, müssen Sie als erstes den gewünschten Parameter auswählen, den gemessenen Wert eingeben und Ihre Initialen hinzufügen. Danach klicken Sie auf "Werte eingeben". Bei fehlenden oder vertauschten Angaben, taucht eine Fehlermeldung auf.')
        st.image("https://scontent-zrh1-1.xx.fbcdn.net/v/t39.30808-6/340814580_873671940393634_1930207743141895922_n.jpg?_nc_cat=106&ccb=1-7&_nc_sid=730e14&_nc_ohc=74hh1K-tpiAAX_dQzoh&_nc_ht=scontent-zrh1-1.xx&oh=00_AfCQG_zqqI7NJN8-41VorgQg0CPARzhZDMl7nkF5JMNXvA&oe=643C77EC")
        st.caption("Bildqulle: Eigene Aufnahme")
    with st.expander("Verlauf der letzten 10 Werte"):
        st.header("Verlauf der letzten 10 Werte")
        st.write("Für die Beurteilung der Qualitätskontrolle, können Sie hier die einzelnen Parmeter anwählen und somit kontrollieren. Die letzten 10 Werte sind in Form einer Tabelle und einer Levey-Jennings-Kurve ersichtlich.")
        st.image("https://scontent-zrh1-1.xx.fbcdn.net/v/t39.30808-6/340783719_963336444835418_4174430397612721810_n.jpg?_nc_cat=108&ccb=1-7&_nc_sid=730e14&_nc_ohc=3pP_VpZG-akAX8v9P3q&_nc_ht=scontent-zrh1-1.xx&oh=00_AfC8ma9lLG9MWWWhghZqxzYikAmos74eLo_QirIXQcCKJg&oe=643C24E7")
        st.caption("Bildqulle: Eigene Aufnahme")
        st.write("Unterhalb der Levey-Jennings-Kurve wird mittels einer Meldung nach der Westgard-Regel beurteilt und dies farbig dargestellt.")
        st.markdown("Falls die Regel: :red[2-2s Regel], :red[1-3s Regel] und :red[R4s Regel] verletzt werden, können Sie mit folgendem Flussdiagramm arbeiten.")

        # Flussdiagramm für Fehlerbehebung
        graph = graphviz.Digraph()
        graph.edge('Westgard-Regel verletzt', ' QK wiederholen')
        graph.edge(' QK wiederholen', 'Westgard-Regel zum 2. Mal verletzt')
        graph.edge('Westgard-Regel zum 2. Mal verletzt', 'Verfallsdatum kontrollieren')
        graph.edge('Verfallsdatum kontrollieren', 'QK wiederholen')
        graph.edge('QK wiederholen','Westgard-Regel zum 3. Mal verletzt')
        graph.edge('Westgard-Regel zum 3. Mal verletzt', 'Reagenzien und QK ersetzen')
        graph.edge('Reagenzien und QK ersetzen',' QK wiederholen ')
        graph.edge(' QK wiederholen ','Kalibration')
        graph.edge('Kalibration', 'Westgard-Regel zum 4. Mal verletzt')
        graph.edge('Westgard-Regel zum 4. Mal verletzt', 'Techniker kontaktieren')

        st.graphviz_chart(graph)
        st.caption("Abkürzung: QK=Qualitätskontrolle,")
