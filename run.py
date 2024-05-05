from mct_app import create_app, db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db, render_as_batch=True)

if __name__ == '__main__':
    app.run()