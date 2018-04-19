from bottle import route, run
from datetime import datetime

@route('/status/<device_id>')
def status(device_id):
   return { "system": 1, "device": str(device_id) }

@route('/time')
def time():
   current_time = datetime.now().isoformat(' ')
   return {"system": 1, "datetime": current_time}

run(host='0.0.0.0', port=8000)
