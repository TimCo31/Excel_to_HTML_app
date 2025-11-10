import streamlit as st
import pandas as pd
import os
from collections import namedtuple
import zipfile
import io
import shutil

def recuperer_nombre_options_et_attributs(df):
    colonnes_options = [col for col in df.columns if col.startswith("option")]
    options = list(set([col.split(".")[0] for col in colonnes_options]))
    attributs = list(set([col.split(".")[1] for col in colonnes_options]))
    Resultat = namedtuple('Resultat', ['options', 'attributs'])
    return Resultat(options, attributs)

def generer_pages_html(df):
    if "Choice" not in df.columns:
        raise ValueError("La colonne 'Choice' est manquante dans le fichier.")
    
    resultat = recuperer_nombre_options_et_attributs(df)
    options = resultat.options
    attributs = resultat.attributs

    if not os.path.exists("situations_html"):
        os.makedirs("situations_html")

    # Copier les images dans le dossier situations_html
    for option in options:
        if os.path.exists(f"temp/{option}.png"):
            shutil.copy(f"temp/{option}.png", f"situations_html/{option}.png")

    template_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Situation {choice}</title>
        <style>
            table {{
                border-collapse: collapse;
                width: 80%;
                margin: 20px auto;
            }}
            th, td {{
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            input[type="checkbox"] {{
                transform: scale(1.5);
                margin: 0 auto;
            }}
            th img {{
                max-width: 100px;
                max-height: 100px;
                display: block;
                margin: 0 auto 5px;
            }}
        </style>
    </head>
    <body>
        <h1 style="text-align: center;">Situation {choice}</h1>
        {table_html}
    </body>
    </html>
    """

    for index, row in df.iterrows():
        choice = row["Choice"]
        table_rows = []

        for attr in attributs:
            row_html = f"<tr><td>{attr}</td>"
            for option in options:
                row_html += f"<td>{row[f'{option}.{attr}']}</td>"
            row_html += "</tr>"
            table_rows.append(row_html)

        choix_row = "<tr><td>Choix</td>"
        for _ in options:
            choix_row += '<td style="text-align: center;"><input type="checkbox"></td>'
        choix_row += "</tr>"
        table_rows.append(choix_row)

        headers = "<th>Attribut</th>"
        for option in options:
            img_tag = ""
            if os.path.exists(f"situations_html/{option}.png"):
                img_tag = f'<img src="{option}.png" alt="{option}" style="max-width: 100px; max-height: 100px; display: block; margin: 0 auto 5px;">'
            headers += f"<th>{img_tag}<br>{option}</th>"

        table_html = f"""
        <table>
            <thead>
                <tr>{headers}</tr>
            </thead>
            <tbody>
                {"".join(table_rows)}
            </tbody>
        </table>
        """




        with open(f"situations_html/situation_{choice}.html", "w") as file:
            file.write(template_html.format(choice=choice, table_html=table_html))

    # Créer une archive ZIP des fichiers HTML
    zip_filename = "situations_html.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("situations_html"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start = "situations_html")
                zipf.write(file_path, arcname)

    return zip_filename

def main():
    st.title("Générateur de Pages HTML pour les Questionnaires")

    uploaded_file = st.file_uploader("Déposez votre fichier Excel ou CSV ici :", type=["xlsx", "csv"])

    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.write("Aperçu des données :")
        st.dataframe(df)

        resultat = recuperer_nombre_options_et_attributs(df)
        options = resultat.options
        images = {}
        for option in options:
            st.subheader(f"Image pour {option}")
            img_file = st.file_uploader(f"Déposez une image pour {option}", type=["png", "jpg", "jpeg"], key=f"img_{option}")
            if img_file is not None:
                img_path = os.path.join("temp", f"{option}.png")
                if not os.path.exists("temp"):
                    os.makedirs("temp")
                with open(img_path, "wb") as f:
                    f.write(img_file.getbuffer())
                images[option] = img_path

        if st.button("Générer les pages HTML"):
            with st.spinner("Génération en cours..."):
                zip_filename = generer_pages_html(df)
            st.success("Génération terminée !")

            with open(zip_filename, "rb") as f:
                st.download_button(
                    label="Télécharger les pages HTML",
                    data=f,
                    file_name=zip_filename,
                    mime="application/zip"
                )

if __name__ == "__main__":
    main()