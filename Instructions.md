# Assort Terminal Intake Agent

## Prereqs
- Python 3.10+ recommended
- An OpenAI API key (provided by Assort)
- A Google Maps API key with **Address Validation API** enabled

## Setup
1) Create and activate a virtual environment:
   - python -m venv .venv
   - source .venv/bin/activate  (macOS/Linux)
   - .venv\Scripts\activate     (Windows)

2) Install dependencies:
   - pip install -r requirements.txt

3) Export environment variables:
   - export OPENAI_API_KEY="YOUR_OPENAI_KEY"
   - export GOOGLE_MAPS_API_KEY="GOOGLE_MAPS_API_KEY"
   - (Check uploaded PDF for Google Maps API Key.)

   (Windows PowerShell)
   - setx OPENAI_API_KEY "YOUR_OPENAI_KEY"
   - setx GOOGLE_MAPS_API_KEY "YOUR_GOOGLE_MAPS_KEY"

## Enable Google Address Validation API
In Google Cloud Console:
- Create/select a project
- Enable “Address Validation API”
- Create an API key and set it as GOOGLE_MAPS_API_KEY

## Run the agent
- python main.py

Type `exit` or `quit` to leave the program.

## Notes on appointment availability (mock data)
Provider list and appointment slots are mocked in `data.py`.
Selections are validated against those mock slots (unavailable slots are rejected).
