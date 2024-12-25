from main import app, production_run_setup

if __name__ == "__main__":
    production_run_setup()
    app.run()