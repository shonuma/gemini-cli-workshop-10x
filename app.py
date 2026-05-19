import os
import logging

from dotenv import load_dotenv
from flask import (Flask, abort, flash, redirect, render_template, request,
                   url_for)
from flask.typing import ResponseReturnValue
from pydantic import ValidationError
from werkzeug.exceptions import NotFound

import database
from models import EventCreateRequest, ResponseModel

# Load environment variables from .env file (for local development)
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


app = Flask(__name__)
# In production, the secret key must be set via the
# FLASK_SECRET_KEY environment variable.
# For local development, ensure it is set in your .env file.
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key and not app.debug:
    raise ValueError("No FLASK_SECRET_KEY set for production environment")


@app.route('/')
def index() -> ResponseReturnValue:
    return render_template('index.html')


@app.route('/create', methods=['POST'])
def create_event() -> ResponseReturnValue:
    try:
        form_data = {
            "event-name": request.form.get('event-name'),
            "description": request.form.get('description', ''),
            "candidate-dates": request.form.getlist('candidate-dates'),
            "password": request.form.get('password')
        }
        event_req = EventCreateRequest.model_validate(form_data)
    except ValidationError as e:
        logger.warning(f"Event validation failed: {e}")
        flash('入力内容に誤りがあります。')
        return redirect(url_for('new_event'))

    event_id = database.create_new_event(event_req)
    return redirect(url_for('event_detail', event_id=event_id))


@app.route('/event/<string:event_id>')
def event_detail(event_id: str) -> ResponseReturnValue:
    res = database.get_event_and_responses(event_id)
    if not res:
        abort(404)

    return render_template('event.html',
                           event=res.event_data.model_dump(),
                           event_id=event_id, candidate_dates=res.candidate_dates, responses=res.responses,
                           date_scores=res.date_scores,
                           best_dates=res.best_dates)


@app.route('/event/<string:event_id>/respond', methods=['POST'])
def respond_to_event(event_id: str) -> ResponseReturnValue:
    data = request.get_json(silent=True)
    if not data:
        return {'status': 'error', 'message': 'Invalid JSON data'}, 400

    try:
        resp_data = ResponseModel.model_validate(data)
        database.save_new_response(event_id, resp_data)
        return {'status': 'success', 'message': '回答を保存しました。'}
    except ValidationError as e:
        logger.warning(f"Response validation failed: {e}")
        return {'status': 'error', 'message': '入力内容に誤りがあります。'}, 400
    except ValueError as e:
        logger.warning(f"Failed to save response: {e}")
        return {'status': 'error', 'message': str(e)}, 400


@app.route('/event/<string:event_id>/delete/<string:response_id>', methods=['POST'])
def delete_response(event_id: str, response_id: str) -> ResponseReturnValue:
    try:
        database.delete_response_from_db(event_id, response_id)
        return {'status': 'success', 'message': '回答を削除しました。'}
    except ValueError as e:
        logger.warning(f"Failed to delete response: {e}")
        return {'status': 'error', 'message': '回答が見つからないか、削除に失敗しました。'}, 404


@app.route('/event/<string:event_id>/delete', methods=['POST'])
def delete_event(event_id: str) -> ResponseReturnValue:
    password = request.form.get('password', '')
    try:
        database.delete_event_from_db(event_id, password)
        flash('イベントが削除されました。')
        return redirect(url_for('index'))
    except ValueError as e:
        flash(str(e))
        return redirect(url_for('event_detail', event_id=event_id))


@app.route('/new')
def new_event() -> ResponseReturnValue:
    return render_template('new.html')


@app.route('/event/list')
def event_list() -> ResponseReturnValue:
    events = database.get_all_events()
    return render_template('list.html', events=events)


@app.errorhandler(404)
def page_not_found(error: NotFound) -> ResponseReturnValue:
    return render_template('404.html'), 404


@app.errorhandler(Exception)
def handle_unexpected_error(error: Exception) -> ResponseReturnValue:
    logger.error(f"Unexpected error occurred: {error}", exc_info=True)
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
