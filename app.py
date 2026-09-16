from backend import create_app
from backend.simulator.simulator import simulate

packets = simulate()

for packet in packets:
    print(packet)

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)