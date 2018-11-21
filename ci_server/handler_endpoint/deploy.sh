# integration
export PYTHONPATH=$PYTHONPATH:`pwd`
export FLASK_ENV=development
connexion run gm_analytics/swagger/indexer.yaml --debug -p 8080
