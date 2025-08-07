from flask import Flask, request, render_template
import psycopg2, requests, os

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "goldbook")
DB_USER = os.getenv("DB_USER", "golduser")
DB_PASS = os.getenv("DB_PASS", "goldpass")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/new-comment")

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)

# Création de la table avec les nouveaux champs si elle n'existe pas
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            comment TEXT NOT NULL,
            summary TEXT,
            sentiment TEXT,
            keywords TEXT[]
        )
        """)
        conn.commit()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form["name"]
        comment = request.form["comment"]

        # Sauvegarde en base (sans summary, sentiment, keywords encore)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO comments (name, comment) VALUES (%s,%s) RETURNING id", (name, comment))
                comment_id = cur.fetchone()[0]
                conn.commit()

        # Déclenchement du webhook n8n, on envoie aussi l'id du commentaire pour update après analyse
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={"id": comment_id, "name": name, "comment": comment},
            auth=('admin', 'admin')  # identifiants n8n
        )

    # Récupération des commentaires avec les champs ajoutés
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, comment, summary, sentiment, keywords FROM comments ORDER BY id DESC")
            comments = cur.fetchall()

    return render_template("index.html", comments=comments)

from flask import jsonify

@app.route("/comments/<int:id>", methods=["PUT"])
def update_comment(id):
    data = request.get_json()

    summary = data.get("résumé")
    sentiment = data.get("sentiment")
    keywords = data.get("mots_clés")  # attends un array

    if not all([summary, sentiment, keywords]):
        return jsonify({"error": "Missing fields"}), 400

    # Connexion DB et update
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE comments
                    SET summary = %s,
                        sentiment = %s,
                        keywords = %s
                    WHERE id = %s
                    RETURNING id, name, comment, summary, sentiment, keywords
                """, (summary, sentiment, keywords, id))
                updated = cur.fetchone()
                conn.commit()

                if updated is None:
                    return jsonify({"error": "Comment not found"}), 404

        # Renvoi de l'update
        updated_comment = {
            "id": updated[0],
            "name": updated[1],
            "comment": updated[2],
            "résumé": updated[3],
            "sentiment": updated[4],
            "mots_clés": updated[5]
        }
        return jsonify(updated_comment), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
