import time
import random
from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
#enable prometheus metrics
metrics = PrometheusMetrics(app)
#custom metric: track "revenue"
revenue_counter = metrics.counter(
'app_revenue_total', 'Total revenue generated', labels ={'product':'standard'}
)
@app.route('/')
def home():
	return jsonify({"status": "healthy","service":"payment-processor"})
@app.route('/checkout')
@revenue_counter
def checkout():
	#simulate a sales of 49.99 usd
	#in a real app, we would increment the value dynamically
	#for this demo, we count the events
	return jsonify({"message": "Order confirmed", "value":49.99})
@app.route('/heavy')
def heavy_load():
	#simulate a slow database queury(latency spike)
	time.sleep(random.uniform(0.5, 2.0))
	return jsonify({"message":"Heavy task complete"})
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
